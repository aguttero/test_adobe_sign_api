import ast

# CONFIG
SECRETS_FOLDER = "./client_secret/"
USER_LIST_FILENAME = f"{SECRETS_FOLDER}user_list.txt"

with open (USER_LIST_FILENAME, "r") as file:
    file_content = file.read()

user_list = ast.literal_eval(file_content)
# print ("user_list:\n", user_list)
print ("len user_list:", len(user_list))
print (f"{user_list[0]}\n{user_list[1]}\n{user_list[len(user_list)-1]}")
print ("*THE END*")