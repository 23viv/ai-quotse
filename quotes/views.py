from django.shortcuts import render, redirect
from django.http import JsonResponse
from pymongo import MongoClient
from groq import Groq
from django.conf import settings

# MongoDB client setup
client = MongoClient('mongodb://localhost:27017/')
db = client['ai_quotes_db']
users_collection = db['users']

def welcome(request):
    return render(request, 'welcome.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        # Check if the user already exists
        if users_collection.find_one({"email": email}):
            return JsonResponse({"error": "User already exists! Please log in."})

        # Save user in the database
        users_collection.insert_one({"username": username, "email": email, "password": password})
        return redirect('login')

    return render(request, 'signup.html')

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        # Authenticate user
        user = users_collection.find_one({"email": email, "password": password})
        if user:
            # Store the user in the session
            request.session['user'] = user['username']
            # Initialize an empty chat history in the session
            request.session['chat_history'] = []
            return redirect('chat')
        else:
            return JsonResponse({"error": "Invalid email or password."})

    return render(request, 'login.html')

# Groq client setup
groq_client = Groq(api_key=settings.GROQ_API_KEY)

def chat(request):
    if request.method == "POST":
        # Parse JSON data from the request
        user_input = request.POST.get("user_input", "").strip()

        if not user_input:
            return JsonResponse({"response": "Please provide a word or phrase to generate quotes."})

        try:
            # Make a request to the Groq API
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Generate 3 quotes based on a given word in a linear format."},
                    {"role": "user", "content": user_input},
                ],
                temperature=1,
                max_tokens=100,
                top_p=1,
                stream=False
            )
            # Extract AI response
            response = completion.choices[0].message.content.strip()

            # Append user input and AI response to chat history
            chat_entry = {"user": user_input, "ai": response}
            if "chat_history" not in request.session:
                request.session['chat_history'] = []
            request.session['chat_history'].append(chat_entry)
            request.session.modified = True  # Mark session as modified to save updates

            return JsonResponse({"response": response})

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"response": "An error occurred. Please try again later."})

    # Pass chat history to the template for rendering
    chat_history = request.session.get('chat_history', [])
    return render(request, "chat.html", {"chat_history": chat_history})
