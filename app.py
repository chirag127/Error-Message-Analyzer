
import streamlit as st
from pymongo import MongoClient
import re
import cohere
from datetime import datetime

co = cohere.Client('PQ50WPjjMsFSzUhZlMQaGTlS30MyRs9YkbuKfhHh')

def get_chatgpt_answer(question):

    return get_cohere_answer(question)



@st.cache_data()
def get_cohere_answer(question):
    """
    This function uses the Cohere API to get an answer for the question
    """

    response = co.generate(
  model='command-nightly',
  prompt="""there are two examples of errors that are already in the database.

Error Example: a cookie header was received [${jndi:ldap://log4shell-generic-8molyf0ab2aqtscsyugh${lower:ten}.w.nessus.org/nessus}=${jndi:ldap://log4shell-generic-8molyf0ab2aqtscsyugh${lower:ten}.w.nessus.org/nessus};] that contained an invalid cookie.

Regex: `a cookie header was received \[.*?\] that contained an invalid cookie\.`

Solution: This regex will help you identify instances where a cookie header is received with an invalid cookie. You should then inspect the actual cookie content to determine the cause of the error.

---

Error Example: servlet.service() for servlet [dispatcherservlet] in context with path [] threw exception

Regex: `servlet\.service\(\) for servlet \[.*?\] in context with path \[\] threw exception`

Solution: This regex will help you identify instances where a servlet named "dispatcherservlet" in a specific context path throws an exception. You should investigate the servlet configuration and the exception stack trace to diagnose and resolve the issue.

---
please suggest a regex for the following error and a brief solution to solve the following error:

New Error: """ + question + """

don't forget to end the response with ---

just provide the two values in the following format:

Regex: <regex to match the error>

Solution: <solution>"""

,
  max_tokens=244,
  temperature=0,
  k=0,
  stop_sequences=["---"],
  return_likelihoods='NONE')
# print('Prediction: {}'.format(response.generations[0].text))
    return response.generations[0].text

# Access MongoDB connection details from Streamlit secrets
db_uri = st.secrets["db_uri"]
db_database = st.secrets["db_database"]
db_collection = st.secrets["db_collection"]

client = MongoClient(db_uri)


dblist = client.list_database_names()
# print("the list of databases are: ", dblist)

if db_database in dblist:
    # print("The database exists.")

    db = client[db_database]

else:
    # print("The database does not exist.")

    db = client[db_database]


# Ensure the collection exists, create it if it doesn't
collection_name = db_collection
if collection_name not in db.list_collection_names():
    db.create_collection(collection_name)

collection = db[collection_name]

def check_known_errors(user_input, category_filter=None, project_filter=None):
    # Define the query filters based on the provided category and project
    query_filters = {}
    if category_filter:
        query_filters["Category"] = category_filter
    if project_filter:
        query_filters["Project"] = project_filter

    # Check if the regex pattern matches any document in the MongoDB collection
    matched_errors = []
    for error_doc in collection.find(query_filters):
        regex_pattern = error_doc["ErrorRegex"]
        if re.search(regex_pattern, user_input, re.IGNORECASE):
            matched_errors.append(error_doc["ErrorSolution"])
    return matched_errors

def add_new_error(user_input, solution, category, project, username):
    # Insert a new document into the MongoDB collection with category, project, username, date, and time
    error_doc = {
        "ErrorRegex": user_input,
        "ErrorSolution": solution,
        "Category": category,
        "Project": project,
        "Username": username,
        "Timestamp": datetime.now(),
    }
    collection.insert_one(error_doc)

def if_submit_button_clicked(new_error_regex, new_error_solution, selected_category, selected_project, user_name):

    if new_error_regex and new_error_solution:
        add_new_error(new_error_regex, new_error_solution, selected_category, selected_project, user_name)
        st.success("New error added to the database!")

def reset_session_state():
    # st.session_state.user_input = ""
    st.session_state.new_error_regex = ""
    st.session_state.new_error_solution = ""

def main():
    # Streamlit app
    st.set_page_config(
        page_title="Error Message Analyzer",
        page_icon="https://lh3.googleusercontent.com/YtXTsa-6SaaMl02-OUo8iRztlX5Thu4aCLavunIV1M5hm9y4ySTPpMjpY44fL4ayz7Se",
    )

    # Containers
    top = st.container()



    # User input for error message
    with top:

        # Add a logo image
        logo_image = 'https://lh3.googleusercontent.com/YtXTsa-6SaaMl02-OUo8iRztlX5Thu4aCLavunIV1M5hm9y4ySTPpMjpY44fL4ayz7Se'  # Replace 'path_to_your_logo_image.png' with the actual path to your logo image

        # Custom header with logo
        header_html = f"""
        <div style="display: flex; align-items: center; padding: 10px;">
            <img src={logo_image} alt="Logo" width="50" height="50" style="margin-right: 10px;">
            <h1>Error Message Analyzer</h1>
        </div>
        """

        st.markdown(header_html, unsafe_allow_html=True)

        # Add title
        # st.title("Error Message Analyzer")

    if "user_input" not in st.session_state:
        st.session_state.user_input = ""
    if "new_error_regex" not in st.session_state:
        st.session_state.new_error_regex = ""
    if "new_error_solution" not in st.session_state:
        st.session_state.new_error_solution = ""


    st.text_area(
        "Enter your error message:", key="user_input", on_change=reset_session_state
    )
    # Dropdowns for selecting category and project
    category_options = ["Devops", "Infra", "Database", "networking", "development", "All"]
    selected_category = st.selectbox("Select Category", category_options, index=len(category_options)-1)

    project_options = ["EAI3535810", "EAI3536166", "EAI3535733", "EAI3535861", "EAI3537167",
                       "EAI3538846", "EAI3531605", "EAI3535858", "EAI3537214", "EAI3538016", "EAI3538118", "All"]
    selected_project = st.selectbox("Select Project", project_options, index=len(project_options)-1)

    if st.button("Check Error") or st.session_state.user_input:
        category_filter = selected_category if selected_category != "All" else None
        project_filter = selected_project if selected_project != "All" else None
        matched_errors = check_known_errors(st.session_state.user_input, category_filter, project_filter)


        if matched_errors:
            st.success("Known Error Detected")
            for error_solution, i in zip(matched_errors, range(len(matched_errors))):
                # Display the error solution in a good format
                st.write(f"Solution {i+1}:", error_solution)

                # solution was added by on 2021-10-20 12:00:00 by user1

                # beutiful_data_time = collection.find_one({"ErrorSolution": error_solution})["Timestamp"].

                st.write("Solution was added by " + str(collection.find_one({"ErrorSolution": error_solution})["Username"]) + " on " + str(collection.find_one({"ErrorSolution": error_solution})["Timestamp"].strftime("%Y-%m-%d %H:%M:%S")))


        else:
            st.header("New Error Detected")
            st.write("This error is not in the database. Would you like to add it?")

            # add a spinner while waiting for the answer
            with st.spinner(
                "Please wait while we suggest a regex and a solution for this error ..."
            ):
                st.session_state.chatgpt_answer = ""
                # get the answer from chatgpt

                try:
                    st.session_state.chatgpt_answer = get_chatgpt_answer(
                        f"""{st.session_state.user_input}"""
                    )

                    print("answer is: ", st.session_state.chatgpt_answer)

                except Exception as e:
                    print("error" + str(e))
                    st.write(
                        "Error in auto-suggesting a regex and a solution for this error. Please provide a regex and a solution manually."
                    )

            # try: to extract the regex and solution from the answer
            try:

                if not st.session_state.new_error_regex:

                    regex = re.search(r"Regex:(.*)\n", st.session_state.chatgpt_answer).group(1).strip().strip("`")
                    st.session_state.new_error_regex = regex

                if not st.session_state.new_error_solution:

                    # remove everything before the solution
                    solution = st.session_state.chatgpt_answer.split("Solution:")[1].strip().strip("`").strip("---").strip()

                    st.session_state.new_error_solution = solution


                # remove the code block from the regex from the start and end if exists



            except Exception as e:
                print("error" + str(e))

                print("error in extracting the regex and solution from the answer")

                st.write(st.session_state.chatgpt_answer)


            with st.form("new_error_form"):
                new_error_regex = st.text_input(
                    "Error Regex (Edit if necessary):",
                    key="new_error_regex",
                )
                new_error_solution = st.text_area(
                    "Error Solution (Provide a solution for the error):",
                    key="new_error_solution",
                    height=300,

                )

                new_selected_category = st.selectbox("Select Category", category_options, index=len(category_options)-1, key="new_selected_category")

                new_selected_project = st.selectbox("Select Project", project_options, index=len(project_options)-1, key="new_selected_project")





                user_name = st.text_input("Enter your username:", key="user_name")

                submit = st.form_submit_button("Submit")

            if submit:

                if_submit_button_clicked(new_error_regex, new_error_solution, new_selected_category, new_selected_project, user_name)




    # st.write("Please reload the page to check another error.")

if __name__ == "__main__":
    main()
