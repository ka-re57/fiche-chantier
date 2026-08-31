# -*- coding: utf-8 -*-
"""Genere la page de demonstration a partir de fiche-chantier/index.html."""
import io, re, os
os.chdir('/home/claude')

src = io.open('fiche-chantier/index.html', encoding='utf-8').read()
titre = re.search(r'<title>.*?</title>', src, re.S).group(0)
style = re.search(r'<style>.*?</style>', src, re.S).group(0)
body  = re.search(r'<body>(.*?)</body>', src, re.S).group(1)

sw_bloc = body[body.index('if("serviceWorker" in navigator){'):body.index('function bandeauMaj(){')]
body = body.replace(sw_bloc, '/* service worker desactive dans la demonstration */\n\n')

import re as _re
body = _re.sub(r'var VERSION = "[^"]+";',
  lambda m: m.group(0)+'\nvar DEMO = true;   /* page de demonstration : aucun envoi reel, donnees fictives */',
  body, count=1)
assert 'var DEMO = true' in body, 'ancre VERSION introuvable'

body = body.replace('function chargerListe(manuel){\n  if(!cfg.webhookListe){',
'''function chargerListe(manuel){
  if(DEMO){
    liste = {maj:new Date().toISOString(), chantiers: CHANTIERS_DEMO.map(normChantier)};
    ecrire(CLE_LISTE, liste);
    if(vue==="accueil") rendre();
    if(manuel) toast(liste.chantiers.length+" chantiers de d\\u00e9monstration charg\\u00e9s","ok");
    return;
  }
  if(!cfg.webhookListe){''')

i_pm = body.index("function postMake(")
j_pm = body.index("{", i_pm)+1
body = body[:j_pm] + """
  if(DEMO){
    return new Promise(function(res){
      setTimeout(function(){ res({ok:true, status:200, text:function(){ return Promise.resolve("demo"); }}); }, 350);
    });
  }""" + body[j_pm:]

_rep_msg = ('if(envoyes){ toast(DEMO ? "D\u00e9monstration \u2014 rien n\'est parti, l\'envoi est simul\u00e9"'
            ' : envoyes+" envoi"+(envoyes>1?"s":"")+" effectu\u00e9"+(envoyes>1?"s":""), DEMO ? "att" : "ok"); }')
body = _re.sub(r'if\(envoyes\)\{ toast\(envoyes\+" envoi"[^;]+; \}',
               lambda m: _rep_msg, body, count=1)
assert "rien n'est parti" in body, 'ancre toast envoi introuvable'

# en demo, le telechargement est bloque par le lecteur d'artefact : on remplace les fonctions
_d = body.index("function telecharger(")
_f = body.index("function exporterFiche(")
body = body[:_d] + """function telecharger(nom, contenu, type){
  montrerTexte("Fichier : "+nom, contenu);
  toast("D\\u00e9monstration : dans la vraie appli, le fichier se t\\u00e9l\\u00e9charge","att");
}
function telechargerTxt(){ telecharger("brief.txt", briefChiffrage()); }

""" + body[_f:]
assert "a.download" not in body, "le lien de telechargement subsiste"

demo = r'''
/* ============================================================
   CHANTIERS DE DEMONSTRATION - noms fictifs, format Axonaut reel
   ============================================================ */
var CHANTIERS_DEMO = [
 {id:5074772, name:"Remplacement chaudière gaz - Marly", pipe_step_name:"a_chiffrer",
  company:{id:50699258, name:"PERRIN Hélène"}, creation_date:"2026-08-26",
  comments:"Remplacement de la chaudière gaz existante. Maison 1976, béton banché non isolé, ~112 m2, radiateurs acier type 22. Adresse exacte à compléter."},

 {id:5042464, name:"MARCHAND Julie - PAC air/eau", pipe_step_name:"contact_recu",
  company:{id:50147022, name:"MARCHAND Julie"}, creation_date:"2026-08-03",
  comments:"DEMANDE RECUE PAR MAIL - NOUVEAU CLIENT\n\nObjet: PAC air/eau\nUrgence: Sous 2 mois\n\nDescription:\nRemplacement chaudière gaz par pompe à chaleur air/eau. Maison 120 m2 de 1998 avec radiateurs classiques.\n\nNom: MARCHAND Julie\nE-mail: julie.marchand@example.fr\nTelephone: 06 22 41 08 73\nAdresse: 14 rue des Vergers 57530 Courcelles-Chaussy\n\nQue faut-il faire : Rappeler pour convenir d'une visite technique et établir un devis\n\nDossier Drive : https://drive.google.com/drive/folders/exemple\n"},

 {id:5043910, name:"LAMBERT Céline - Salle de bain", pipe_step_name:"contact_recu",
  company:{id:50169702, name:"LAMBERT Céline"}, creation_date:"2026-08-04",
  comments:"DEMANDE RECUE PAR MAIL - NOUVEAU CLIENT\n\nObjet: Salle de bain\nUrgence: Non precisee\n\nDescription:\nRénovation de salle de bain dans une maison de 2005. Demande de passage pour établir un devis.\n\nNom: LAMBERT Céline\nE-mail: c.lambert@example.fr\nTelephone: 06 45 12 87 30\nAdresse: 7 impasse des Lilas 57365 Ennery\n\nQue faut-il faire : Prendre rendez-vous pour visite et établir un devis\n"},

 {id:5042108, name:"BERTIN Laurence - devis climatisation", pipe_step_name:"contact_recu",
  company:{id:50142364, name:"BERTIN Laurence"}, creation_date:"2026-08-03",
  comments:"Type de demande:devis\nUrgence: projet_futur\nDisponibilités: À partir de mi-septembre\n\nDescription:Étude de l'installation d'un système de climatisation, 4 pièces à traiter\n\nNom:BERTIN Laurence\nE-mail: l.bertin@example.fr\nTéléphone: 06 71 19 15 54\nAdresse: 12 rue des Pinsons\nVille:57640 Argancy\nType de logement: maison\nest-il bien le proprietaire: Propriétaire\nQue faut-il faire : Rappeler - Devis climatisation maison\n"},

 {id:5044468, name:"Devis climatisation + douche", pipe_step_name:"a_chiffrer",
  company:{id:46182238, name:"ROUSSEL Michel et Catherine"}, creation_date:"2026-08-04",
  comments:"Devis clim air/air + douche. ALLER SUR PLACE avant de chiffrer. TVA clim : 5,5 % depuis le 18/07/2026 si l'appareil remplit les criteres."},

 {id:9999, name:"Chantier terminé - ne doit pas apparaître", pipe_step_name:"termine",
  company:{id:1, name:"EXEMPLE Ancien client"}, creation_date:"2026-01-01", comments:""}
];
'''
body = body.replace('var ETAPES_OK =', demo + '\nvar ETAPES_OK =')

body = body.replace('setTimeout(function(){ viderFile(false); chargerListe(false); }, 1500);',
 'if(DEMO && !liste.chantiers.length) chargerListe(false);\nsetTimeout(function(){ viderFile(false); }, 1500);')

body = body.replace('<div id="toast" role="status" aria-live="polite"></div>',
 '<div id="toast" role="status" aria-live="polite"></div>\n'
 '<div id="demoBandeau">Démonstration — données fictives, aucun envoi réel</div>')

style = style.replace('</style>',
'''#demoBandeau{
  position:fixed;left:0;right:0;bottom:0;z-index:90;
  background:var(--att);color:#fff;font-family:var(--ui);font-weight:600;
  font-size:12px;letter-spacing:.05em;text-align:center;padding:3px 8px;pointer-events:none;
}
.actions{bottom:20px}
main{padding-bottom:150px}
</style>''')

io.open('fiche-chantier-demo.html','w',encoding='utf-8').write(titre + "\n" + style + "\n" + body)
print("demo regeneree :", os.path.getsize('fiche-chantier-demo.html'), "octets")
