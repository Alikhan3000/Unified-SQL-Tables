# main.py
class SimpleChatbot:
    def __init__(self):
        self.name = "Assistant"
        print(f"Hello! I'm {self.name}. Type 'quit' to exit.")
    
    def get_response(self, user_input):
        """Simple response logic"""
        user_input = user_input.lower().strip()
        
        # Simple greeting responses
        if any(word in user_input for word in ['hello', 'hi', 'hey']):
            return "Hello! How can I help you today?"
        
        # Simple product questions
        elif any(word in user_input for word in ['product', 'item', 'buy']):
            return "I can help you find products! Try asking 'show me electronics'"
        
        # Simple user questions
        elif any(word in user_input for word in ['user', 'customer', 'find']):
            return "I can search for users! Try asking 'find user John'"
        
        # Help command
        elif 'help' in user_input:
            return """I can help you with:
            - Finding products (try: 'show me electronics')
            - Searching users (try: 'find user John')
            - General questions
            """
        
        # Default response
        else:
            return "I'm sorry, I don't understand. Type 'help' to see what I can do."
    
    def start_chat(self):
        """Main chat loop"""
        while True:
            user_input = input("\nYou: ")
            
            # Exit condition
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye! Have a great day!")
                break
            
            # Get and display response
            response = self.get_response(user_input)
            print(f"{self.name}: {response}")

# Run the chatbot
if __name__ == "__main__":
    chatbot = SimpleChatbot()
    chatbot.start_chat()
