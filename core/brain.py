class Brain:
    def __init__(self, config, conversation):
        self.identity = config["identity"]
        self.conversation = conversation

    def respond(self, message):
        self.conversation.add_user_message(message)

        response = self.generate_response()

        self.conversation.add_butler_message(response)

        return response

    def generate_response(self):
        last_message = self.conversation.get_messages()[-1]["content"]

        if "hello" in last_message.lower():
            return "Hello. I'm Butler."

        if "my name is" in last_message.lower():
            return "It's nice to meet you."

        if "what did i just tell you" in last_message.lower():
            messages = self.conversation.get_messages()

            previous_messages = [
                message["content"]
                for message in messages[:-1]
                if message["role"] == "user"
            ]

            if previous_messages:
                return f"You previously told me: {previous_messages[-1]}"

        return "I hear you."