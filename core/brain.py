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

            lower_content = content.lower()

            if lower_content.startswith("my favorite ") and " is " in lower_content:
                subject_and_value = content[len("My favorite "):]
                subject, value = subject_and_value.split(" is ", 1)

                value = value.rstrip(".")

                self.memory.save_memory(
                    content=content,
                    category="preference",
                    subject=subject.strip(),
                    value=value.strip(),
                )
            else:
                self.memory.save_memory(content=content)

            return f"Remembered: {content}"
        
        if "what do you remember about me" in last_message.lower():
            if self.memory is None:
                return "I don't have access to personal memory."

            memories = self.memory.get_memories()

            if memories:
                return " ".join(memory["content"] for memory in memories)

            return "I don't have any personal memories stored."

        if self.memory is not None:
            memories = self.memory.find_relevant_memories(
                query=last_message
            )

            if memories:
                return memories[0]["content"]


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
