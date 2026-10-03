class Brain:
    def __init__(self, config, conversation, memory=None):
        self.identity = config["identity"]
        self.conversation = conversation
        self.memory = memory

    def respond(self, message):
        self.conversation.add_user_message(message)

        response = self.generate_response()

        self.conversation.add_butler_message(response)

        return response

    def generate_response(self):
        last_message = self.conversation.get_messages()[-1]["content"]
        
        if last_message.lower().startswith("remember:"):
            if self.memory is None:
                return "I don't have access to personal memory."

            content = last_message.split(":", 1)[1].strip()

            if not content:
                return "There is nothing to remember."

            self.memory.save_memory(content=content)
            return f"Remembered: {content}"
        
        if "what do you remember about me" in last_message.lower():
            if self.memory is None:
                return "I don't have access to personal memory."

            memories = self.memory.get_memories()

            if memories:
                return " ".join(memory["content"] for memory in memories)

            return "I don't have any personal memories stored."


        if "favorite college" in last_message.lower():
            if self.memory is None:
                return "I don't have access to personal memory."

            memories = self.memory.search_memories(query="college")

            if memories:
                return memories[0]["content"]

            return "I don't have that information stored."


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
