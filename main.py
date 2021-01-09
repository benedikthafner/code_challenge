# Built-in Imports
import json
import copy
import webbrowser
import os

__author__ = "Benedikt Hafner"
__version__ = "1.0"
__maintainer__ = "Benedikt Hafner"
__email__ = "benedikt_hafner@icloud.com"
__status__ = "Dev"
__about__ = "Antwort auf die BWI Coding Challenge >>Code for BWI<<."

# Import der Daten
with open('./data_input.json') as f:
  data = json.load(f)

# Vorbereiten der Datenstruktur (Python Dictionary) für das Ergebnis
transport = {
    "trucks": [],
    "total_utility": 0
}

for truck in data['_meta'].get('trucks'):
    truck_data = {
        "id": truck['id'],
        "products_to_load": [],
        "rest_weight": data['_meta'].get('max_weight') - truck.get("driver_weight"),
        "truck_utility": 0
    }
    transport['trucks'].append(truck_data)

# Berechnung des Nutzwerts pro Gramm
for product in data.get('products'):
    product['utility_per_weight'] = product.get('utility')/product.get('weight') #check for zero-division

# Absteigende (= reverse) Sortierung der Produkte nach Nutzwert pro Gramm
data['products'] = sorted(data.get('products'), key=lambda k: k['utility_per_weight'], reverse=True)

# Zuordnung der Produkte mit optimalen Nutzwert zu den Transportern:
for truck in transport['trucks']:
    for product in data['products']:
        if product['number'] == 0:
            # Alle Einheiten des Produkts wurden bereit in einem Transporter untergebracht.
            pass
        else:
            # Berechnung der Anzahl an Einheiten in den Transporter passen.
            num_prod_fit = int(truck['rest_weight']/product['weight']) 
            if num_prod_fit > 0:
                if num_prod_fit > product['number']:
                    truck['rest_weight'] -= product['number']*product['weight']
                    truck['truck_utility'] += product['number']*product['utility']
                    truck['products_to_load'].append(copy.deepcopy(product))
                    product['number'] = 0
                else:
                    product_to_load = copy.deepcopy(product)
                    product_to_load['number'] = num_prod_fit
                    truck['products_to_load'].append(product_to_load)
                    truck['rest_weight'] -= num_prod_fit*product['weight']
                    truck['truck_utility'] += num_prod_fit*product['utility']
                    product['number'] -= num_prod_fit
            else:
                # Das Produkt ist zu schwer um eine Einheit im Transporter unterbringen zu können.
                pass

# Der Nutzwert kann weiter verbessert werden, indem Produkte mit mit optimalem Nutzwert/Gewicht-Verhältnis
# durch etwas schwerere Produkte mit höherem Nutzwert eingetauscht (= swap) werden.
# Dafür müssen alle Produkte die Beladen werden sollten nocheinmal 
# mit den übriggebliebenen Produkten verglichen werden.

# Die while-Schleife wird so lange Durchlaufen bis bei einem Durchlauf 
# keine mögliche Tauschvorgänge gefunden werden können.
while 1:
    swap_list = []
    swap_flag = False
    for truck in transport['trucks']:
        for product in truck['products_to_load']:
            for remaining_product in data['products']:
                # Die Kriterien: 
                # - Durch einen Tausch würde die maximale Ladelast nicht überschritten.
                # - Der Nutzwert wird durch den Tausch erhöht.
                if remaining_product['number'] > 0 and \
                    truck['rest_weight'] + product['weight'] >= remaining_product['weight'] and \
                    product['utility'] < remaining_product['utility']:

                    swap_element = {
                        "to_replace": product['id'],
                        "replacement": remaining_product['id'],
                        "utility_plus": remaining_product['utility'] - product['utility'],
                        "weight_plus": remaining_product['weight'] - product['weight'],
                        "truck": truck['id']
                    }
                    swap_list.append(swap_element)
                else:
                    pass

    # Pro Durchlauf der While-Schleife wird der beste Tausch ermittelt. 
    # Der beste Tausch ist der Tausch mit dem größten Gewinn an Nutzwert (= utility plus).
    if len(swap_list) > 0:
        # Sortieren der Liste möglicher Tausche nach Nutzen; Nur Tausch mit höchstem Nutzen wird durchgeführt.
        best_swap = sorted(swap_list, key=lambda k: k['utility_plus'], reverse=True)[0]

        # Updaten der übrig gebliebenen Produkte
        ## Die next-Funktion wird genutzt um den Index eines Produktes anhand der ID finden zu können.
        ## Indizes können sich durch das Sortieren ändern. Die IDs bleiben gleich. 
        remaining_product_increase = \
            next(i for i, item in enumerate(data['products']) if item["id"] == best_swap['to_replace'])
        data['products'][remaining_product_increase]['number'] +=1
        remaining_product_decrease = \
            next(i for i, item in enumerate(data['products']) if item["id"] == best_swap['replacement'])
        data['products'][remaining_product_decrease]['number'] -=1

        # Updaten der zu tauschenden Produkte
        products_to_load = transport['trucks'][best_swap['truck']]['products_to_load']
        transport['trucks'][best_swap['truck']]['rest_weight'] -= best_swap['weight_plus']
        transport['trucks'][best_swap['truck']]['truck_utility'] += best_swap['utility_plus']
        products_to_load_increase = \
            next((i for i, item in enumerate(products_to_load) if item["id"] == best_swap['replacement']), None)
        
        # Falls das Produkt bisher noch nicht in der Ausgabe-Datenstruktur noch nicht vorhanden ist,
        # wird es neu angelegt.
        if products_to_load_increase == None:
            product_to_load = copy.deepcopy(data['products'][remaining_product_decrease])
            product_to_load['number'] = 1
            products_to_load.append(product_to_load)
        else:
            products_to_load[products_to_load_increase]['number'] +=1
        products_to_load_decrease = \
            next((i for i, item in enumerate(products_to_load) if item["id"] == best_swap['to_replace']), None)
        
        # Falls die letzte Einheit eines Produkts getauscht wird,
        # muss das Produkt aus der Ausgabe-Datenstruktur entfernt werden.
        if products_to_load[products_to_load_decrease]['number'] ==1:
            del products_to_load[products_to_load_decrease]
        else:
            products_to_load[products_to_load_decrease]['number'] -=1
    else:
        for truck in transport['trucks']:
            transport['total_utility'] += truck['truck_utility']
        break


## Zur Ausgabe der Ergebnisse wird eine HTML-Seite erstellt. 
# Hierfür wird eine Vorlage geladen. Die Vorlage verwendet Bootstrap.css zur schöneren Formatierung.
with open('./template.html') as h:
  html_template = h.read()

# Die Vorlage wird in einer Liste aus Strings zwischengespeichert und um Tabellen-Elemente erweitert.
html_template = html_template.split('###')
for truck in transport['trucks']:
    html_template.insert(-1, 
    '<thead><tr><th colspan="4">Transporter {} mit einem Gesamtgewicht (Fahrer und Ladung) von {}kg:</th></tr></thead><thead><tr><th scope="col">Anzahl Einheiten</th><th scope="col">Produktname</th><th scope="col">Gewicht, in g</th><th scope="col">Nutzwert</th><th scope="col">Nutzwert/Gramm</th></tr></thead><tbody>'
    .format(truck['id'], (data['_meta']['max_weight'] - truck['rest_weight'])/1000))
    for product in truck['products_to_load']:
        html_template.insert(-1,
            '<tr><th scope="row">{}</th><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
            product['number'], 
            product['name'], 
            product['weight'], 
            product['utility'], 
            round(product['utility_per_weight'],3)))            
    html_template.insert(-1, '</tbody>')

# Speichern der Ergebnisse als HTML-Dokument.
html_output = open("Lieferschein.html", "w+")
n = html_output.write(''.join(html_template))
html_output.close()
webbrowser.open('file://' + os.path.realpath('Lieferschein.html'))

# Speichern Informationen über die zuverladenen Produkte als JSON.
json_transport_output = open("data_transport_output.json", "w+")
n = json_transport_output.write(json.dumps(transport, indent = 4, sort_keys=True))
json_transport_output.close()

# Speichern Informationen über der übriggebliebenen Produkte als JSON.
json_leftover_output = open("data_leftover_output.json", "w+")
n = json_leftover_output.write(json.dumps(data, indent = 4, sort_keys=True))
json_leftover_output.close()

# Die Lösung der Aufgabe wird über das Command-line Interface.
# Der Lieferschein dient nur der Veranschaulichung.
print("Der kumulierte Nutzen beträgt: {}.".format(transport['total_utility']))
print("Der Lieferschein (Lieferschein.html) für die ermittelte Ladung kann im Browser betrachtet werden.")