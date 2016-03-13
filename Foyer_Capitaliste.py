import sys
import requests
import copy
import math
import time
import threading
from tkinter import *
from autocomplete import AutocompleteEntry
import matplotlib.pyplot as plt


#Initialisation:login
prices=[1.0]
down_rate=0.03  #le prix d'une biere baissera de down_rate%
up_rate=0.25 #le prix d'une biere montera de up_rate%
down_limit=-0.1#si la biere passe en dessous de -down_limit(>0), alors on met son rpix en negatif a down_limit
make_me_positive=0.3#lorsqu'une biere est en negatif et que quelqu'un la prend, alors elle passe nettement en positif au prix make_me_positive
upont="https://upont.enpc.fr/api";
username=input("username:")
password=input("password:")
user_list={}
beer_list={}
user=""
beer=""
login_request=requests.post(upont+"/login",{"username":username,"password":password})
token=login_request.json()["token"]
if(math.floor(login_request.status_code/100)==2):
    print("Connected")
else:
    print("Connection failed")


def sync_price(beer):
    json_bieres2=copy.deepcopy(json_bieres)
    if(beers_names_activate[beer].get()):#on check que la biere est bien dans le jeu
        for i in range(0,len(json_bieres)-1):
            if(beers_names_activate[json_bieres[i]["slug"]].get()):#si la biere est dans le jeu
                json_bieres2[i].pop("slug")
                requests.patch(upont+"/beers/"+json_bieres[i]["slug"],json=json_bieres2[i],headers={"Authorization":"Bearer "+token})
    print("Prix changés")
    
def change_price(beer):
    json_bieres2=copy.deepcopy(json_bieres)
    if(beers_names_activate[beer].get()):#on check que la biere est bien dans le jeu
        for i in range(0,len(json_bieres)-1):
            if(beers_names_activate[json_bieres[i]["slug"]].get()):#si la biere est dans le jeu
                if(json_bieres[i]["slug"]==beer):#si la biere est celle commandee on augmente le prix
                    if(json_bieres[i]["price"]>0):
                        json_bieres[i]["price"]=(1+up_rate)*json_bieres[i]["price"]
                    else:
                        json_bieres[i]["price"]=make_me_positive #si la biere etait a prix negatif, et que quelqu'un la prend, elle repasse en positif
                else:#si ce n'est pas celle consommee on baisse le prix
                    if(json_bieres[i]["price"]*(1-down_rate)>-down_limit):
                        json_bieres[i]["price"]=(1-down_rate)*json_bieres[i]["price"]
                    else:
                        json_bieres[i]["price"]=down_limit
    beers_prices.append([[i["slug"],i["price"]] for i in json_bieres])#on enregistre le nouvel etat des prix
    t=threading.Thread(target=sync_price,args=(beer,))
    t.start();
        
def reinit_price(json_biere_init):
    for i in range(0,len(json_biere_init)-1):
        beer=json_biere_init[i]["slug"]
        json_bieres_init[i].pop("slug")
        requests.patch(upont+"/beers/"+beer,json=json_bieres_init[i],headers={"Authorization":"Bearer "+token})

def put_conso(user,beer):
    if(beers_names_activate[beer].get()):
        order_request=requests.post(upont+"/transactions",headers={"Authorization":"Bearer "+token},data={"user":user,"beer":beer})
        if(math.floor(order_request.status_code/100)==2):
            print("OK: "+user)
        else:
            print("Error with: "+user)
        time.sleep(0.005)
    else:
        print("Cette biere a ete desactivee!")
        
def get_users():
    user_request=requests.get(upont+"/users?limit=10000",headers={"Authorization":"Bearer "+token})
    if(math.floor(user_request.status_code/100)==2):
        print("Users data downloaded")
        user_json=user_request.json()
        user_names_slug=[[i["first_name"].capitalize()+" "+i["last_name"].capitalize(),i["username"]] for i in user_json]
        return user_names_slug
    else:
        print("Error downloading users data: "+str(user_request.status_code)+".")
        
def get_beers():
    beers_request=requests.get(upont+"/beers",headers={"Authorization":"Bearer "+token})
    if(math.floor(beers_request.status_code/100)==2):
        print("Beers data downloaded")
        json_bieres=beers_request.json()
        json_bieres2=copy.deepcopy(json_bieres)
        for i in range(0,len(json_bieres2)-1):#la requete patch de l'API permettant de modifier une biere est stricte sur le contenu du JSON
            for j in json_bieres2[i]:
                if(j!="name" and j!="price" and j!="alcohol" and j!="volume" and j!="image" and j!="slug"):
                    json_bieres[i].pop(j)
        return json_bieres
    else:
        print("Error downloading beers data: "+str(beers_request.status_code)+".")

def quit(json_bieres_init):
    plt.close("all")
    print("Reinitialisation des prix...")
    reinit_price(json_bieres_init)
    print("Termine")
    sys.exit()
    



user_names_slug=get_users()
json_bieres=get_beers()
json_bieres_init=copy.deepcopy(json_bieres)
beers_names_activate=dict((i["slug"],0) for i in json_bieres)
beers_prices=[[[i["slug"],i["price"]] for i in json_bieres]]#on stocke ici l'evolution des prix de toutes les bieres


window=Tk()
j=0
k=0
list_checkboxes=[]
for i in beers_names_activate:
    beers_names_activate[i]=BooleanVar()
    list_checkboxes.append(Checkbutton(window, text=i, variable=beers_names_activate[i]))
    list_checkboxes[len(list_checkboxes)-1].grid(row=k,column=j)
    j+=1
    if(j%3==0):
        k+=1
        j=0
    

def callback_button_order(autocomplete_users,autocomplete_beers):
    put_conso(user_names_slug[[i[0] for i in user_names_slug].index(autocomplete_users.get())][1],autocomplete_beers.get())
    change_price(autocomplete_beers.get())    
    t=threading.Thread(target=plot_prices,args=(beers_prices,beers_names_activate,graphs))
    t.start();
        
    
def callback_set_beers(autocomplete_beers,autocomplete_users,beers_prices,json_bieres,json_bieres_init):
    for i in list_checkboxes:
        i.grid_remove()
    button_hide.grid_remove()
    for i in json_bieres:
        if not(beers_names_activate[i["slug"]].get()):
            json_bieres.remove(i)
    for i in json_bieres_init:
        if not(beers_names_activate[i["slug"]].get()):
            json_bieres_init.remove(i)
    for i in beers_prices[0]:
        if not(beers_names_activate[i[0]].get()):
            beers_prices[0].remove(i)
    autocomplete_users.grid(row=0)
    autocomplete_beers.grid(row=1)
    button_order.grid(row=2)
    for j in range(0,len(beers_prices[0])-1):
        if(beers_names_activate[beers_prices[0][j][0]].get()):
            graphs.append(plt.figure("prix "+beers_prices[0][j][0]))
    
   
    
def plot_prices(beers_prices,beers_names_activate,graphs):

    i=0
    for j in range(0,len(beers_prices[0])-1):
        if(beers_names_activate[beers_prices[0][j][0]].get()):
            plt.figure("prix "+beers_prices[0][j][0])
            plt.plot([i[j][1] for i in beers_prices if(beers_names_activate[i[j][0]].get())])
            plt.draw()
            i+=1
    

graphs=[]
plt.ion()
autocomplete_users=AutocompleteEntry([k[0] for k in user_names_slug],window)
autocomplete_beers=AutocompleteEntry([k[0] for k in beers_prices[0]],window)
button_order=Button(window,text="Investir",command=lambda:callback_button_order(autocomplete_users,autocomplete_beers))
button_hide=Button(window,text="Valider liste bieres",command=lambda:callback_set_beers(autocomplete_beers,autocomplete_users,beers_prices,json_bieres,json_bieres_init))
button_hide.grid(row=k+1,column=k+1)
plt.show()
window.mainloop()
quit(json_bieres_init)




