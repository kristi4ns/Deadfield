#!/usr/bin/python
# _*_ coding: UTF-8 _*_


#pylist = ["I AM body","I AM Girl","I AM treen "]
#for  data  in pylist:
#    print data 
#count = 0
#while count < len(pylist):
#    print(pylist[count])
#    count = count+1
#movies = ["The Holy Grail",1975, "Terry Jones & Terry Gilliam",91,
#             ["Graham Chapman",["Michael Palin","John Cleese",
#                 "Terry Gilliam","Eric Idle","Terry Jones"]]]
#print movies
#for each_item in movies:
#    print(each_item)     

def print_lol(the_list,indent=False,level=0):
    for each_item in the_list:
        if isinstance(each_item,list):
            print_lol(each_item,indent,level+1)
    else:
        if indent:
             for tab_stop in range(level):
                print ("\t\n")
        print(each_item)

#print_lol(movies) 
