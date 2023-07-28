from creator import handleURL, defaultParams
import json

id = input("enter user id: ")
with open(f"static\\PosterStorage\\user{int(id)}\\data.json", 'r') as handle:
    data = json.load(handle)
    for item in data:
        if data[item]['type'] == "album":
            handleURL(f"album/{item}?", defaultParams, "/user"+str(id))
        else:
            handleURL(f"playlist/{item}?", defaultParams, "/user"+str(id))
    handle.close()