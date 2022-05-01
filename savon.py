#%%
from pathlib import Path
from configparser import ConfigParser
import numpy as np
import pandas as pd
import json
from datetime import date

recette = Path.cwd() / 'recette.ini'
moules_file = Path().cwd() / 'moules.json'
with open(moules_file, 'r') as mf:
    moules = json.load(mf)


#recette = Path(r'C:\Users\ltestut\PycharmProjects\mishi\recette.ini')

def get_ptf(config,moules):
    "recupere le poids total du savon du fichier moules"
    return moules[config['IDENTITE']['moule']]['poids_savon']

def volume_moule(config):
    "calcul du volume du moule en cm3"
    dims = float(config['MOULE']['longueur'])*float(config['MOULE']['largeur'])\
           *float(config['MOULE']['hauteur'])
    return dims

def verification_huiles(config):
    "verifie que les quantités d'huile sont bien egales = 100 %"
    sum = 0
    for huile in config['HUILES'] :
        sum+=int(config['HUILES'][huile])
    return True if sum == 100 else False

def somme_liquides(config,verbose=False):
    "calcul de la somme des liquides en pourcentage "
    sum = 0
    for i in config['LIQUIDES']:
        if verbose :
            print(f"       {i} = {config['LIQUIDES'][i]} %")
        sum+=float(config['LIQUIDES'][i])
    return sum

def get_pth(config):
    "Calcul du poids total des huiles à partir du poids total final"
    ptf = volume_moule(config)   #poids total final = volume du moule
    surgras = float(config['IDENTITE']['surgras'])/100. # en pourcentage
    coef_saponification_moyen = 0.139 #il dépend des huiles utilisées
    denominateur = (1+somme_liquides(config)/100.)+(1-surgras)*coef_saponification_moyen
    return ptf/denominateur

def calcul_soude(config,surgras=None): #TODO a refaire il est faut
    "calcul du poid total de la soude "
    pth = get_pth(config)
    huiles = config['HUILES']
    if surgras is None :
        surgras = float(config['IDENTITE']['surgras'])
    sum = 0.
    for x in huiles:
        q_huile = float(huiles[x]) / 100. * pth  # quantite d'huile en grammes
        q_soude = float(config['COEF'][x])*q_huile #quantite de soude pour cette huile
        print(f" quantité de soude pour {x} = {q_soude:.1f} gr")
        sum+=q_soude
    print(f" quantite de soude avec {surgras}% de surgras ="
          f" {(1 - surgras/100.) * sum: .1f}")
    return round(np.floor((1 - surgras/100.)*sum))

def update_recette(config):
    "mise à jour de la recette avec les quantités calculées"
    huiles = config['HUILES']
    liquides = config['LIQUIDES']
    # ajout des quantites
    config['QUANTITE']['Volume du moule   '] = f"{volume_moule(config)/1000.:.3f} litre "
    config['QUANTITE']['Poid Total Savon  ']  = f"{round(volume_moule(config))} gr # 1 litre = 1 kg"
    for x in liquides:
        config['QUANTITE'][x] = f"{round(float(liquides[x]) / 100. * pth)} gr"
    config['QUANTITE']['Poid Total Huiles ']  = f"{round(get_pth(config))} gr "
    for x in huiles:
        config['QUANTITE'][x] = f"{round(float(huiles[x]) / 100. * pth)} gr"
    config['QUANTITE']['soude'] = f"{calcul_soude(config)} gr"
    output_name = config.filename.as_posix().replace('recette',config['IDENTITE']['nom'])
    with open(Path(output_name).with_suffix('.txt'), 'w') as configfile:
        config.write(configfile)
    print(f"mise à jour des calcule dans {Path(output_name).with_suffix('.txt')}")

def verion_html(config):
    "ecriture dans un fichier pandas DataFrame puis dans un html"
    pth = round(get_pth(config))
    d={'PTS':[np.nan,round(volume_moule(config))],
       '#savons':[round(volume_moule(config))/120,np.nan],
       'PTH':[100,pth],
       'surgras':[config['IDENTITE']['surgras'],np.nan]}
    huiles = config['HUILES']
    liquides = config['LIQUIDES']
    sum_liq = 0
    d.update({'Huiles--':['---','---']})
    for i in huiles:
        gr_hui = [huiles[i],round(float(huiles[i]) / 100. * pth)]
        d.update({i: gr_hui})
    d.update({'Liquides--': ['---', '---']})
    for i in liquides :
        gr_liq = [liquides[i],round(float(liquides[i]) / 100. * pth)]
        sum_liq += gr_liq[1]
        d.update({i:gr_liq})
    d.update({'Total liquide':[np.sum([int(liquides[i]) for i in liquides]),sum_liq]})
    d.update({'Soude--': ['---', round(calcul_soude(config))]})
    df = pd.DataFrame(index=d.keys(),data=d.values(),columns=['%','grammes'])
    df.index.name=config['IDENTITE']['nom']
    output_name = Path(config.filename.as_posix().replace('recette', config['IDENTITE']['nom'])).with_suffix('.html')
    df.to_html(output_name)
    print(f"ecriture du fichier {output_name}")
    return df

#%% lancement du programme
# 1. lecture de la recette
config=ConfigParser()
if recette.exists() :
    print(f"lecture du fichier {recette}")
    config.read(recette)
    config.filename = recette #ajout du nom de fichier dans la parser
    moule, surgras  = config['IDENTITE']['moule'],float(config['IDENTITE']['surgras'])
    huiles, liquides, coef = config['HUILES'], config['LIQUIDES'], config['COEF']
    volume = volume_moule(config)
    ptf    = round(volume)
else :
    print(f"le fichier {recette} n'existe pas")

#%% 2. information
#calcul du PTF à partir du volume du moule
print(f" Recapitulatif pour la recette {config['IDENTITE']['nom'].upper()} à {surgras}% de surgras du {date.today()}")
print(f"    1. PTF theorique = {ptf} gr (cm3) pour un moule de dim :"
      f" L={config['MOULE']['longueur']}cm/l={config['MOULE']['largeur']}cm/H={config['MOULE']['hauteur']}cm ")
print(f"       PTF observee  = {get_ptf(config,moules)} gr pour le moule {moule}")
print(f"           soit {moules[moule]['nbr_savons']} savons de {moules[moule]['poids_unite']} gr ")
print(f"    2. Liquides contenu dans le savon ")
pliq=somme_liquides(config,verbose=True)
print(f"       Total Liquides {pliq} %")

#verification de la quantite d'huile et calcul des quantites
if not verification_huiles(config) :
    print(f" ATTENTION la somme des huiles ne fait pas 100 %")
else :
    print(f"   2.  Composition des huiles ")
    pth  = get_pth(config)
    soude = 0
    for x in huiles:
        huile = float(huiles[x])/100.*pth #quantite d'huile en grammes
        soude += float(coef[x])*huile     #quantite de soude
        print(f"  * {x:>15} = {huiles[x]}% soit {huile:.1f} gr et soude={float(coef[x])*huile:.1f} gr")
    print(f"quantite total de soude avant retrait : {soude:.1f}")
    print(f"quantite soude avec {surgras}% de surgras : {(1-surgras/100.)*soude:.1f}")

#%% MISE A JOUR DU FICHIER RECETTE
update_recette(config)
df=verion_html(config)
