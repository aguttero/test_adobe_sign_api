cursor = {'name':'nombre'}
print ("cursor: ",cursor)
# cursor:  {'name': 'nombre'}

if cursor:
    print("if cursor:", __name__)    

if not cursor:
    print ("if not cursor: ", True)
# if cursor: __main__