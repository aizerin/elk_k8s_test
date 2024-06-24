# CO UMIME TED NA CLUSTERU - STAVAJICI RESENI

- elasticsearch
  - (OK) ror
  - (OK) certifikaty
  - (OK) rolling restart
  - (OK) monitoring logy
  - (OK) monitoring metriky
  - konfigurace
- kibana
  - (OK) ror
  - (OK) monitoring logy
  - (OK) monitoring metriky
  - nginx proxy na breadcrumbs
  - konfigurace
- apm-server
  - instalace (OK)
  - nginx proxy na overeni jwt tokenu
  - konfigurace
- filebeat
  - sber logu z clusteru ze vsech sluzeb
- metricbeat
  - sber metriky z clusteru ze vsech sluzeb
- logstash
  - konfigurace
  - (ok) nahravani pipeline dle konfigurace
    - (ok) pozor nektere pipeline potrebuji i zavisloti na db driveru
  - (ok) dead letter queue a posilani chybnych dat do clusteru
  - (ok) nejaky patch ssl (neni uz potreba)

# CO UMIME TED S TERRAFORMEM - STAVAJICI RESENI

- konfigurace ILM
- zalozeni rolling indexu
- zalozeni index template pro index
- zalozeni kibana space
- zalozeni kibana index pattern
- zalozeni kibana tagu
- nastaveni kibana advanced settings

# NOVE RESENI

- rozjete dva clustery
  - MAIN - hlavni elk cluster
    - zakladni basic auth (x-pack free)
    - vsechny sluzby mohou byt pripojeni na nej primo bez ROR. Kazda sluzba muze mit unikatniho uzivatele
  - ROR - proxy cluster
    - kibana pro koncove uzivatele
    - overeni pres ldap
- monitoring pomoci filelebatu a metricbeatu skrze ECK
  - oba elasticy
  - obe kibany
  - logstash
- logstash
  - pipeliny se buildi jako init container
    - mame tam hodne dat, tak nebylo mozne mit vsechno v secretu
    - sql drivery, grog patterny apod soucasti
    - seznam pipeline ale musi byt jako secret aby s tim umel pracovat ECK
  - zmeny o proti puvodnimu reseni
    - konfigurace cca stejna, jen se neco prejmenovalo nebo doplnilo
      - validace vstupnich dat
    - prepnute na datastreamy, ale ne vse jde. takze podporujeme oboje
    - kvuli data streamum bude jine pojmenovani indexu (s teckama)
      - logs-xxx.yyy-lm
    - ne datastreamy ale nemuzou byt pojmenovane stejne. tzn je to opacne
      - lm-xxx.yyy-logs
    - vsechny hesla v secretu
- apm-server
  - vicemene stejne jako predtim, neni tu nic zajimaveho
- tri oddelene charty (je to spis pro lepsi oddeleni konfigurace)
  - eck-chart - slouzi pro instalaci a nastaveni ECK. je to samostatny operator nezavisly na svem okoli
  - elk-stack - slouzi ke konfiguraci samotneho stacku
    - soucasti jsou pak dva oddelene chart pro ror a main
    - ty se pak externalizuji a v eck-stack bude jen konfigurace specificka pro prostredi
  - elk-stack-monitoring - filebeat a metricbeat pro monitoring clusteru

# TODO

- jak budete resit secrety ? dnes mame v ansiblu viditelne pro vsechny
  - budeme mit secrety z nejkaeho toho password manager
  - nebo self sealed
  - nebo jak mame ted viditelne pro vsechny
  - otazka na kolik je to vubec potreba teda
- presmerovat pak na nase registry
- zkusit zmigrovat indexy z dev prostredi
- jak to chceme koncipovat s namespacema. cheme mit jeden namespace elk. jak to mam ted. nebo namespace per ECK, MAIN a ROR ? ja myslim ze to nejak nehraje roli
  - v ramci jednoho NS muzeme jednoduse sdilet secrety apod
- nastavit cross cluster search v terraformu
- prometheus metriky, chceme ? viz stack monitoring
- odstranit ROR admin account
  - a udelat ror ucty pres secrety

# stack monitoring

- https://www.elastic.co/guide/en/cloud-on-k8s/current/k8s-stack-monitoring.html
- zakladni nastaveni pres monitoring je tak ze on pro kazdy pod udela sidecard container s metricbeatem a filebeatem
  - zere to resources navic
  - zapne logovani do toho podu na filesystem
  - nakonec tohle reseni zamitnuto
  - https://www.elastic.co/guide/en/cloud-on-k8s/current/k8s_when_to_use_it.html
- filebeate a metricbeaty jako daemonset pro monitoring clusteru
  - nastaveni je trochu neintuitivni
    - na druhou stranu je jednoduche tam pridat dalsi veci
    - daleko jednodusi nez vsude konfigurovat sidecontainer
  - filebeat se mne nepodarilo omezit jen na elk namespace jinak nez pres processor
    - jinak pak nefungujou filebeat hinty
    - s tim processorem to je ale tak ze on nabira vsechno a dropuje to mist toho aby nabiral jen co potrebuje
- to budeme mit monitoring jako od ELKU ale cheme i neco dalsiho. prometheus ?
  - koukal jsem ze jsou nejaky prometheus pluginy jako exportery pro ten elk
  - nebo kam budeme primarne koukat misto zabbixu ?
  - https://www.searchhub.io/monitor-elasticsearch-in-kubernetes-using-prometheus
- monitoring samotneho ECK
  - ma primo nejaky prometheus export na zapnuti
  - https://www.elastic.co/guide/en/cloud-on-k8s/current/k8s-enabling-the-metrics-endpoint.html

# TLS

- aktualne se pouzivaji self signed certs managovane by ECK pro https i transport
  - ten si resi vsechno, obnovu certifikatu apod
  - pokud nekdo bude chtit pristoupit na elk rest, kibanu apod tak to bude vystaveno pres ingress. kde si certifikat uz resi balancer a ten je vadlidni dle cpas CA
  - reseni pomoci cert manageru je mimo hru, zadneho nemame :)
- zaver tedy je ze aktualni stav je ok a self signed mezi clusterem nevadi.
  - pokud nekdo by chtel komunikovat primo se servisou v clusteru tak si vezme certak ze secretu (takto to automaticky dela ECK taky)
- two way SSL ROR a MAIN cluster
  - toto je automaticky vyreseno v placene verzi ECK...
  - takze abychom to nemuseli delat rucne a hlidat validitu certifikatu. tak jsem nasel workaround takovy ze pouziju stejny transport certifikat pro ROR cluster i MAIN. necham eck zalozit cert pro MAIN a pouziju stejny secret pro ROR. ECK pak automaticky vytvori remote certifikat stejny pro oba dva clustery.

# TODO ECK OPERATOR

- validacni web hook by sel pouzit k overeni spravnosti konfigurace
  - mohl by to kontrolovat jenkins a proste by v PR spadnul build a nesel mergnout
  - https://www.elastic.co/guide/en/cloud-on-k8s/current/k8s-webhook.html
  - nekolikrat se mne uz stalo ze jsem mel spatnou konfiguraci a ne hned si toho clovek vsimne. hook by urcite usetril cas

# TODO ELASTICSEARCH KONFIGURACE

- porovnat co vse mame zapnute ted na clusteru s tim co se zapina v k8s a jestli to ma/nema smysl pouzit
  - urcite veci se asi budou chovat jinak takze to nebude 1:1 hlavne s tim ECK
- nevim jestli pak nenastavit maxSurge na 1 pro jistotu https://www.elastic.co/guide/en/cloud-on-k8s/current/k8s-update-strategy.html
- pod affinity https://www.elastic.co/guide/en/cloud-on-k8s/current/k8s-advanced-node-scheduling.html#k8s_a_single_elasticsearch_node_per_kubernetes_host_default
  - default je to jak chceme. ale jak to funguje vlastne... chceme rict ktery pod ma jit na ktery stroj a nebo si to poresi sam automaticky ?
  - asi bychom tam meli zapnout to requiredDuringSchedulingIgnoredDuringExecution kdyz by spadnul host at se to nezacne reschedulovat
  - tohle pak asi bude souviset s tema volume a affinitou https://www.elastic.co/guide/en/cloud-on-k8s/current/k8s-advanced-node-scheduling.html#k8s_local_persistent_volume_constraints
- high prioty classy ? https://medium.com/@KushanJanith/run-elastic-stack-on-kubernetes-29e295cd6531
- navod na definici uzivatelu bez ROR https://www.elastic.co/guide/en/cloud-on-k8s/current/k8s-users-and-roles.html
  - dle dokumentace ale lepsi pouzit k ovladani rest api (tedy terraform)
  - ted jak je to v POC jako plain password je shit, lepsi bude vygenerovat ty hashe
- vyzkouset jak to je s userama a rolema. jestli lze mit vice secretu a nebo to ma byt jeden

# Logstash

- TODO script co overi ze je zalozeny datastream pres terraform
  - on si ho size logstash zalozi sam, ale pak bychom meli problem tam nejak docpat tu retenci dat pres terraform. nemeli bychom se ceho chytnout
  - obdoba toho co je ted v index_checker v puvodnim reseni
- OK init container
  - nakopcit lib drivery
  - nakopcit patterny
  - nakopcit static filtry
- TODO pak se musi refactorovat puvodni reseni na nove
  - neni to nic hrozneho, jen se upravej inputy, outputy a prejmenuji se nazvy
- TODO nastavit PVC na DLQ a index sql databaze
  - longhorn ?
  - logstash nejak ma neco default, tak mrknout na to jak to funguje
- OK nejak pak sloucit pipeliny s document id
- TODO sloucit pipeliny kde je jen rozdilne heslo na DB (prod/nonprod)
- TODO hesla pres secrety
- vyzkouset ruzne druhy pipeline
  - OK datastream
  - OK index
  - OK dlq
  - TODO mssql
  - TODO ojdbc
  - TODO grok

# TODO kibana

- mame tam vlastni nginx pro treb breadcrumbs, to bude potreba prenest
  - monitoring toho nginx
- overit breadcrumbs na nove kibane, nemusi fungovat

# TODO apm-server

- prenest konfiguraci
- tady se bude muset prenest konfigurace z toho vlastniho nginx na overeni tokenu
  - a pak ho vystavit pres ingress
  - monitoring toho nginx
- jinak to nebude zadna veda

# TODO terraform

- prepnout na oficialni provider
- zalozit indexy uz pres datastreamy
  - ale nejspis vsechno tak nepujde. myslim ze tam mame i nejake non timeseries takze musime umet udelat stare a i nove reseni\
  - pro datastreamy uz nepouzivat ILM ale ty jejich buildin retention policy (od verze 8.11 jako technical preview)
- kibana
  - tam mame dost nastaveni a vlastniho providera
  - mrknout jestli neni uz neco oficialniho taky

# INSTALACE ROR

- ofiko example https://github.com/sscarduzio/elasticsearch-readonlyrest-plugin/blob/develop/docker-envs/eck/kind-cluster/ror/es.yml
  - neni k tomu oficialni dokumentace
  - na strankach maji zmineno "This feature is in currently in alpha - ETA is Q1’24"
  - dle changelogu tam jsou ruzne fixy pro tohle reseni, takze to je aktivni
  - ssl si jiz nezajistuje ror ale x-pack, takze se to dosti zjednodusuje
  - funguje to dobre, nijak jsem s tim nemel problem

# MIGRACE DAT

- je nutne migrovat ? kdybychom nastavili intercluster komunikaci ze stareho elku tak by to po dobu retence mohlo fungovat ?

# ODKAZY

- ECK CRDS https://www.elastic.co/guide/en/cloud-on-k8s/current/k8s-api-reference.html
- ECK HELM OPERATOR https://github.com/elastic/cloud-on-k8s/blob/2.12/deploy/eck-operator/values.yaml
- ECK HELM STACK https://github.com/elastic/cloud-on-k8s/tree/2.12/deploy/eck-stack
- nejake alerty k inspiraci https://github.com/sapcc/helm-charts/blob/master/system/elk/templates/prometheus-alerts.yaml
