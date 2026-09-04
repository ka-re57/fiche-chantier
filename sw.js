/* Service worker — Fiche chantier KA-RÉ
   La page elle-même : réseau d'abord, cache en secours -> on a toujours la dernière version,
   et ça marche quand même hors connexion.
   Les icônes et le manifeste : cache d'abord, ils ne changent presque jamais. */
var CACHE = "kare-chantier-v1-1";
var FICHIERS = ["./","./index.html","./manifest.webmanifest","./icon-192.png","./icon-512.png","./icon-maskable-512.png"];

/* --- CORRECTIF TEMPORAIRE, 01/09/2026 ---------------------------------
   Un champ de saisie de type numerique AVALE la virgule : 2,5 y devient 25,
   sans alerte. Releve fausse d'un facteur 10. Le vrai correctif est la v2.9
   d'index.html ; en attendant qu'elle soit deposee, on retouche ici le code
   servi, ce qui evite de republier 280 Ko depuis un chantier.
   A RETIRER au depot de la v2.9 : remettre ce fichier d'origine, cache v1-0.
   -------------------------------------------------------------------- */
var RETOUCHES = [
  ['i.type=type||"text";',
   'i.type="text";if(type==="number")i.setAttribute("inputmode","decimal");'],
  ['i.type=(q.t==="num")?"number":"text";',
   'i.type="text";if(q.t==="num")i.setAttribute("inputmode","decimal");'],
  ['iD.type="number";', 'iD.type="text";'],
  ['iA.type="number";', 'iA.type="text";'],
  ['i.type="number";', 'i.type="text";']
];

function poser(html){
  if(html.indexOf("champNombre") !== -1) return html;   /* v2.9 posee : ne rien faire */
  for(var i=0; i<RETOUCHES.length; i++){
    html = html.split(RETOUCHES[i][0]).join(RETOUCHES[i][1]);
  }
  return html;
}

function estLaPage(r){
  return r.mode === "navigate" || (r.destination === "document") ||
         /\/(index\.html)?(\?|$)/.test(new URL(r.url).pathname + new URL(r.url).search);
}

self.addEventListener("install", function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){ return c.addAll(FICHIERS); }).catch(function(){}));
  self.skipWaiting();
});

self.addEventListener("activate", function(e){
  e.waitUntil(
    caches.keys().then(function(k){
      return Promise.all(k.map(function(n){ return n===CACHE ? null : caches.delete(n); }));
    }).then(function(){ return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function(e){
  var r = e.request;
  if(r.method !== "GET") return;                       /* jamais les POST vers Make */
  var u = new URL(r.url);
  if(u.origin !== self.location.origin) return;        /* jamais le trafic externe */

  if(estLaPage(r)){
    /* réseau d'abord : la mise à jour arrive dès qu'il y a du signal */
    e.respondWith(
      fetch(r).then(function(f){
        if(!f || f.status !== 200) return f;
        return f.text().then(function(t){
          var h = new Headers(f.headers);
          h.set("Content-Type", "text/html; charset=utf-8");
          var rep = new Response(poser(t), {status:f.status, statusText:f.statusText, headers:h});
          caches.open(CACHE).then(function(c){ c.put("./index.html", rep.clone()); }).catch(function(){});
          return rep;
        }).catch(function(){ return f; });
      }).catch(function(){
        return caches.match("./index.html").then(function(rep){ return rep || caches.match("./"); });
      })
    );
    return;
  }

  /* le reste : cache d'abord, rafraîchi en arrière-plan */
  e.respondWith(
    caches.match(r).then(function(rep){
      var reseau = fetch(r).then(function(f){
        if(f && f.status === 200){
          var copie = f.clone();
          caches.open(CACHE).then(function(c){ c.put(r, copie); });
        }
        return f;
      }).catch(function(){ return rep; });
      return rep || reseau;
    })
  );
});
