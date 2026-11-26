"""Deterministic review signals for locally imported email."""

import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from verification.evidence import Evidence


RULES = (
    (
        "credential_request",
        re.compile(r"\b(?:verify|enter)\s+your\s+password\b", re.IGNORECASE),
        "Matched wording commonly used to request credentials.",
    ),
    (
        "payment_request",
        re.compile(r"\b(?:wire\s+transfer|gift\s+cards?)\b", re.IGNORECASE),
        "Matched wording associated with payment requests.",
    ),
)

ACCOUNT_SIGN_IN_SUBJECT = re.compile(
    r"(?:your (?:[\w-]+ ){0,5}account was used to sign in to (?P<service>.+?)"
    r"(?: via (?P<sign_in_method>.+?))?"
    r"|new sign[ -]in to your account"
    r"|new device logged in from (?P<platform>[^\s.!](?:.*?[^\s.!])?))[.!]?",
    re.IGNORECASE,
)

PASSWORD_RESET_SUBJECT = re.compile(
    r"(?:password reset request(?:ed)?|reset (?:your )?password)[.!]?",
    re.IGNORECASE,
)

PASSWORD_CHANGE_SUBJECT = re.compile(
    r"(?:your password (?:was|has been) changed|password changed|your password has been updated"
    r"|your (?:[\w-]+ ){1,5}password has been changed)[.!]?",
    re.IGNORECASE,
)

NOTICE_SUBJECTS = (
    ("account_sign_in_notice", ACCOUNT_SIGN_IN_SUBJECT),
    ("password_reset_notice", PASSWORD_RESET_SUBJECT),
    ("password_change_notice", PASSWORD_CHANGE_SUBJECT),
)


URGENT_SUBJECT = re.compile(r"\burgent\b", re.IGNORECASE)
UPDATE_OR_RENEWAL_SUBJECT = re.compile(r"\b(?:update|renew|renewal)\b", re.IGNORECASE)
ACTION_LINK_LABEL = re.compile(
    r"(?:update (?:now|payment)|renew now)", re.IGNORECASE
)


HOME_WARRANTY_SUBJECT = re.compile(r"\bhome warranty\b", re.IGNORECASE)
QUOTE_LINK_LABEL = re.compile(r"get (?:a|my|your) free quote(?:\s*→)?", re.IGNORECASE)


SENSITIVE_SUBJECT = re.compile(
    r"\b(?:sign[ -]in|log[ -]in|verify (?:your )?(?:account|password)"
    r"|reset (?:your )?password|(?:update|confirm|make) (?:your )?(?:a )?payment)\b",
    re.IGNORECASE,
)


DOMAIN_PATTERN = re.compile(
    r"(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}",
    re.IGNORECASE | re.ASCII,
)


class LinkDomainParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.label_parts = []
        self.links_compared = 0
        self.mismatches = []
        self.action_links = []
        self.cloud_page_links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.label_parts = []

    def handle_data(self, data):
        if self.href is not None:
            self.label_parts.append(data)

    def handle_endtag(self, tag):
        if tag != "a" or self.href is None:
            return

        href = self.href
        self.href = None
        label = " ".join("".join(self.label_parts).split())

        try:
            destination = urlsplit(href)
            destination_domain = destination.hostname
        except ValueError:
            return

        if destination.scheme not in {"http", "https"} or not destination_domain:
            return

        if ACTION_LINK_LABEL.fullmatch(label):
            self.action_links.append((label, destination_domain.rstrip(".")))
        if (
            destination_domain.rstrip(".") == "storage.googleapis.com"
            and destination.path.lower().endswith((".htm", ".html"))
        ):
            self.cloud_page_links.append(label)
        displayed_domain = label.lower()
        if DOMAIN_PATTERN.fullmatch(displayed_domain):
            self.links_compared += 1
            if destination_domain != displayed_domain:
                self.mismatches.append((displayed_domain, destination_domain))


class HTMLBodyTextParser(HTMLParser):
    """Collect text nodes without rendering or resolving resources."""

    ignored_tags = {"head", "script", "style", "template"}
    separators = {"br", "div", "p", "li", "tr", "td", "section", "hr"}

    def __init__(self):
        super().__init__()
        self.parts = []
        self.ignored = []

    def handle_starttag(self, tag, attrs):
        if tag in self.ignored_tags:
            self.ignored.append(tag)
        elif not self.ignored and tag in self.separators:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if self.ignored:
            if tag == self.ignored[-1]:
                self.ignored.pop()
        elif tag in self.separators:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


def brand_sender_findings(subject, from_domain, brand_sender_domains):
    if not from_domain or not SENSITIVE_SUBJECT.search(subject):
        return

    sender_domain = from_domain.lower().rstrip(".")
    for brand, expected_domains in brand_sender_domains.items():
        if not re.search(rf"(?<!\w){re.escape(brand)}(?!\w)", subject, re.IGNORECASE):
            continue
        if sender_domain in expected_domains:
            continue
        yield {
            "category": "brand_sender_domain_mismatch",
            "confidence": "low",
            "reason": "The subject names a configured brand and requests a sensitive action from an unexpected sender domain.",
            "evidence": {
                "brand": brand,
                "subject": subject,
                "from_domain": from_domain,
                "expected_domains": sorted(expected_domains),
                "source_type": "local_email",
                "verification_status": "unverified",
            },
        }


def assess_email(
    message_id, message, *, from_domain=None, reply_to_domain=None, html_body=None,
    claimed_address=None, approved_senders=(), sender_domain_authentication=None,
    plain_text_available=True, brand_sender_domains=None,
):
    """Return a JSON-ready assessment without external verification."""
    findings = []
    phrase_fields = [("subject", message["subject"])]
    if plain_text_available:
        phrase_fields.append(("body", message["body"]))

    html_phrase_check = {"status": "skipped", "reason": "html_body_unavailable"}
    if html_body is not None:
        parser = HTMLBodyTextParser()
        parser.feed(html_body)
        parser.close()
        phrase_fields.append(("html_body_text", "".join(parser.parts)))
        html_phrase_check = {"status": "checked"}
    for category, pattern, reason in RULES:
        for field, value in phrase_fields:
            match = pattern.search(value)
            if match is None:
                continue
            evidence = Evidence(
                claim=f"The imported {field} contains the matched phrase.",
                content=match.group(),
                source_type="local_email",
            )
            findings.append({
                "category": category,
                "confidence": "low",
                "reason": reason,
                "evidence": {
                    "field": field,
                    "excerpt": evidence.content,
                    "source_type": evidence.source_type,
                    "verification_status": evidence.verification_status,
                },
            })
            break

    reply_to_check = {"status": "compared"}
    if not (from_domain and reply_to_domain):
        reply_to_check = {
            "status": "skipped",
            "reason": "from_or_reply_to_domain_unavailable",
        }
    elif from_domain != reply_to_domain:
        findings.append({
            "category": "reply_to_domain_mismatch",
            "confidence": "low",
            "reason": "The Reply-To domain differs from the From domain.",
            "evidence": {
                "from_domain": from_domain,
                "reply_to_domain": reply_to_domain,
                "source_type": "local_email",
                "verification_status": "unverified",
            },
        })

    html_check = {
        "status": "skipped",
        "reason": "html_body_unavailable",
        "links_compared": 0,
    }
    if html_body is not None:
        parser = LinkDomainParser()
        parser.feed(html_body)
        parser.close()
        html_check = {"status": "compared", "links_compared": parser.links_compared}
        if not parser.links_compared:
            html_check.update(status="skipped", reason="no_eligible_links")
        for displayed_domain, destination_domain in parser.mismatches:
            findings.append({
                "category": "link_domain_mismatch",
                "confidence": "low",
                "reason": "The link label and destination show different domains.",
                "evidence": {
                    "displayed_domain": displayed_domain,
                    "destination_domain": destination_domain,
                    "source_type": "local_email",
                    "verification_status": "unverified",
                },
            })

        subject = message["subject"]
        urgent_update = URGENT_SUBJECT.search(subject) and UPDATE_OR_RENEWAL_SUBJECT.search(subject)
        if from_domain and urgent_update:
            sender_domain = from_domain.lower().rstrip(".")
            for label, destination in parser.action_links:
                if destination == sender_domain or destination.endswith("." + sender_domain):
                    continue
                findings.append({
                    "category": "urgent_action_external_link",
                    "confidence": "low",
                    "reason": "An urgent update or renewal directs action outside the claimed sender domain.",
                    "evidence": {
                        "subject": subject,
                        "link_label": label,
                        "from_domain": from_domain,
                        "destination_domain": destination,
                        "source_type": "local_email",
                        "verification_status": "unverified",
                    },
                })
                break

        for label in parser.cloud_page_links:
            if urgent_update and not from_domain and label.casefold() == "update payment":
                category = "urgent_payment_cloud_page"
                reason = "An urgent payment update links to a cloud-hosted HTML page and the From address is unusable."
            elif (
                HOME_WARRANTY_SUBJECT.search(subject)
                and QUOTE_LINK_LABEL.fullmatch(label)
                and from_domain
                and from_domain.lower().rstrip(".") != "storage.googleapis.com"
            ):
                category = "home_warranty_quote_cloud_page"
                reason = "A home warranty quote links to a cloud-hosted HTML page outside the claimed sender domain."
            else:
                continue
            findings.append({
                "category": category,
                "confidence": "low",
                "reason": reason,
                "evidence": {
                    "subject": subject,
                    "link_label": label,
                    "from_domain": from_domain,
                    "destination_domain": "storage.googleapis.com",
                    "source_type": "local_email",
                    "verification_status": "unverified",
                },
            })
            break

    if brand_sender_domains:
        findings.extend(brand_sender_findings(message["subject"], from_domain, brand_sender_domains))

    recognized = []
    for category, pattern in NOTICE_SUBJECTS:
        notice = pattern.fullmatch(message["subject"].strip())
        if notice is None:
            continue
        details = {
            field: value
            for field, value in notice.groupdict().items()
            if value is not None
        }
        recognized.append({
            "category": category,
            "details": details,
            "evidence": {
                "field": "subject",
                "excerpt": message["subject"],
                "source_type": "local_email",
                "verification_status": "unverified",
            },
        })

    return {
        "version": "1.0",
        "sender_domain_authentication": sender_domain_authentication or {
            "status": "not_checked",
            "reason": "dkim_verification_not_requested",
        },
        "sender_trust": {
            "claimed_address": claimed_address,
            "approved_address_match": claimed_address in approved_senders,
            "status": "unverified",
            "reason": (
                "trusted_authentication_unavailable" if claimed_address is not None
                else "claimed_address_unavailable"
            ),
        },
        "recognized": recognized,
        "message_id": message_id,
        "disposition": "review_required" if findings else "inconclusive",
        "confidence": "low",
        "reason": (
            "Review the findings and verify requests through a trusted channel."
            if findings else "No supported risk signals were found. Message risk remains unknown."
        ),
        "findings": findings,
        "checks": {
            "plain_text_body": (
                {"status": "checked"} if plain_text_available else
                {"status": "skipped", "reason": "plain_text_body_unavailable"}
            ),
            "reply_to_domains": reply_to_check,
            "html_link_domains": html_check,
            "html_body_phrases": html_phrase_check,
        },
        "limitations": [
            "Phrase matching can miss risks or match benign text.",
            "HTML body phrases use extracted text without evaluating CSS or rendering.",
            "The assessment checks phrases in the subject and available bodies, and compares available From and Reply-To domains.",
            "The HTML link check compares domain-only labels with HTTP or HTTPS destination hostnames without opening links.",
            "Sender identity and message claims were not verified.",
        ],
    }
