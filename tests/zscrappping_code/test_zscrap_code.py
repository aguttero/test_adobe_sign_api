cursor = {'name':'nombre'}
print ("cursor: ",cursor)
# cursor:  {'name': 'nombre'}

if cursor:
    print("if cursor:", __name__)    

if not cursor:
    print ("if not cursor: ", True)
# if cursor: __main__

api_user_list = []

if not api_user_list:
    print ("api_user_list está vacía")
else:
    print ("existe")
    
