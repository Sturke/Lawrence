class Brain:
    def __init__(self, config):
        self.identity = config["identity"]
        self.conversation = []

    def respond(self, message):
        self.conversation.append({
            "role": "user",
            "content": message
        })

        response = self.generate_response()

        self.conversation.append({
            "role": "butler",
            "content": response
        })
        return response

    def generate_response(self):
        last_message = self.conversation[-1]["content"]

        if "hello" in last_message.lower():
            return "Hello. I'm Butler."

        if "my name is" in last_message.lower():
            return "It's nice to meet you."

        if "what did i just tell you" in last_message.lower():
            previous_messages = [
                message["content"]
                for message in self.conversation[:-1]
                if message["role"] == "user"
            ]

            if previous_messages:
                return f"You previously told me: {previous_messages[-1]}"

        return "I've got this."