import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.title("Library Management")

# Sidebar navigation
page = st.sidebar.selectbox("Select a page", ["Books", "Users", "Loans"])

# Books Page
if page == "Books":
    st.header("Books")

    # Fetch and display books
    def fetch_books():
        response = requests.get(f"{API_URL}/books/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch books")
            return []

    books = fetch_books()
    for book in books:
        st.write(f"**{book['title']}** by {book['author']} (ISBN: {book['isbn']})")

    # Add a new book
    st.subheader("Add a New Book")
    book_title = st.text_input("Title")
    book_author = st.text_input("Author")
    book_description = st.text_input("Description")
    book_isbn = st.text_input("ISBN (optional)")

    if st.button("Add Book"):
        new_book = {
            "title": book_title,
            "author": book_author,
            "description": book_description,
            "isbn": book_isbn
        }
        response = requests.post(f"{API_URL}/books/", json=new_book)
        if response.status_code == 200:
            st.success("Book added successfully")
        else:
            st.error("Failed to add book")
            st.error(response.json())  # Print the error message

# Users Page
elif page == "Users":
    st.header("Users")

    # Fetch and display users
    def fetch_users():
        response = requests.get(f"{API_URL}/users/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch users")
            return []

    users = fetch_users()
    for user in users:
        st.write(f"**{user['name']}** ({user['email']})")

    # Add a new user
    st.subheader("Add a New User")
    user_name = st.text_input("Name")
    user_email = st.text_input("Email")

    if st.button("Add User"):
        new_user = {
            "name": user_name,
            "email": user_email
        }
        response = requests.post(f"{API_URL}/users/", json=new_user)
        if response.status_code == 200:
            st.success("User added successfully")
        else:
            st.error("Failed to add user")
            st.error(response.json())  # Print the error message

# Loans Page
elif page == "Loans":
    st.header("Loans")

    # Fetch and display loans
    def fetch_loans():
        response = requests.get(f"{API_URL}/loans/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch loans")
            return []

    loans = fetch_loans()
    for loan in loans:
        st.write(f"Book ID: {loan['book_id']}, User ID: {loan['user_id']}, Return Date: {loan['return_date']}")

    # Add a new loan
    st.subheader("Add a New Loan")
    loan_book_id = st.number_input("Book ID", min_value=1)
    loan_user_id = st.number_input("User ID", min_value=1)
    loan_return_date = st.date_input("Return Date")

    if st.button("Add Loan"):
        new_loan = {
            "book_id": loan_book_id,
            "user_id": loan_user_id,
            "return_date": loan_return_date.isoformat()
        }
        response = requests.post(f"{API_URL}/loans/", json=new_loan)
        if response.status_code == 200:
            st.success("Loan added successfully")
        else:
            st.error("Failed to add loan")
            st.error(response.json())  # Print the error message