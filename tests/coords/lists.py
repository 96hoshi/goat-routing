aachen_coordinates = [
    (
        "50.770933,6.082717",  # Hauptbahnhof (Main Station)
        "50.790961,6.051419",  # Uniklinik (University Hospital)
    ),
    (
        "50.778523,6.078499",  # Pontstraße (Student Area)
        "50.776092,6.088325",  # Elisenbrunnen (City Landmark)
    ),
    (
        "50.793744,6.096389",  # Tivoli (Football Stadium)
        "50.773516,6.085022",  # Bushof (Central Bus Station)
    ),
    (
        "50.786522,6.059288",  # Campus Melaten (University)
        "50.774438,6.083818",  # Aachen Cathedral (Dom)
    ),
    (
        "50.774438,6.083818",  # Aachen Cathedral (Dom)
        "50.753800,6.021000",  # Vaalserberg / Drielandenpunt (Tri-border point NL/BE/DE)
    ),  # Cross-border trip to a major tourist spot (~5 km)
    (
        "50.776092,6.088325",  # Elisenbrunnen
        "50.783100,6.096100",  # Carolus Thermen (Spa)
    ),  # A classic wellness route within the city
    (
        "50.770933,6.082717",  # Hauptbahnhof
        "50.755400,6.160100",  # Aachen-Brand (Eastern district)
    ),  # Long-distance trip across the city (~7 km)
    (
        "50.785081,6.110543",  # Europaplatz (Major roundabout)
        "50.784500,6.101300",  # Ludwig Forum (Art Museum)
    ),
    (
        "50.773824,6.098418",  # Normaluhr (Timepiece landmark)
        "50.738000,6.090000",  # Aachener Wald (Forest for recreation)
    ),  # City center to nature
    (
        "50.779776,6.069904",  # RWTH Main Building
        "50.793700,6.102300",  # CHIO Aachen (World Equestrian Festival grounds)
    ),  # University to a major event location
    (
        "50.790961,6.051419",  # Uniklinik
        "50.770933,6.082717",  # Hauptbahnhof (Return trip)
    ),
    (
        "50.767073,6.102148",  # Burtscheid (Spa district)
        "50.778523,6.078499",  # Pontstraße (Student Area)
    ),
    (
        "50.778255,6.062013",  # Vaalser Straße (near Dutch border)
        "50.785081,6.110543",  # Europaplatz
    ),
    (
        "50.763445,6.115856",  # Station Rothe Erde
        "50.779776,6.069904",  # RWTH Library
    ),
]
mannheim_coordinates = [
    (
        "49.487459,8.466039",  # Mannheim Hauptbahnhof
        "49.489590,8.467236",  # Wasserturm Mannheim
    ),  # Hbf → Wasserturm
    (
        "49.484330,8.475690",  # Universität Mannheim
        "49.488110,8.464900",  # Paradeplatz
    ),  # Uni → Paradeplatz
    (
        "49.482800,8.464200",  # Schloss Mannheim
        "49.495200,8.461800",  # Neckarstadt-West
    ),  # Schloss → Neckarstadt-West
    (
        "49.489590,8.467236",  # Wasserturm
        "49.492000,8.479000",  # Luisenpark
    ),  # Wasserturm → Luisenpark
    (
        "49.487459,8.466039",  # Hauptbahnhof
        "49.463300,8.525500",  # SAP Arena (major event venue)
    ),  # Hbf → SAP Arena (~5 km)
    (
        "49.488110,8.464900",  # Paradeplatz
        "49.481500,8.445500",  # Ludwigshafen Rathaus (across the Rhine)
    ),  # Paradeplatz → Ludwigshafen (~2 km)
    (
        "49.482800,8.464200",  # Schloss Mannheim
        "49.493900,8.455400",  # Jungbusch (trendy district)
    ),  # Schloss → Jungbusch
    (
        "49.489590,8.467236",  # Wasserturm
        "49.477700,8.502900",  # Technoseum
    ),  # Wasserturm → Technoseum (~3 km)
    (
        "49.495200,8.461800",  # Neckarstadt-West
        "49.524400,8.490000",  # Waldhof (northern district)
    ),  # Neckarstadt-West → Waldhof (~4 km)
    (
        "49.484330,8.475690",  # Universität Mannheim
        "49.467800,8.529200",  # Maimarktgelände (fairgrounds)
    ),  # Uni → Maimarktgelände (~5 km)
    (
        "49.403200,8.694200",  # Heidelberg Hbf
        "49.468100,8.456800",  # Rheinau (south Mannheim)
    ),  # Heidelberg → Rheinau (~20 km)
    (
        "49.489590,8.467236",  # Wasserturm
        "49.538300,8.574100",  # Viernheim (outside Mannheim, reachable by tram)
    ),  # Wasserturm → Viernheim
    (
        "49.484330,8.475690",  # Universität Mannheim
        "49.468100,8.456800",  # Rheinau (southern Mannheim)
    ),  # Uni → Rheinau
    (
        "49.495200,8.461800",  # Neckarstadt-West
        "49.521000,8.530000",  # Käfertal Zentrum (northern Mannheim, reachable by tram/bus)
    ),  # Neckarstadt-West → Käfertal
]

germany_coordinates = [
    # --- Long Distance Routes (> 20 km) ---
    (
        "52.525592,13.369545",  # Berlin Hauptbahnhof
        "48.140228,11.558330",  # München Hauptbahnhof
    ),  # Berlin Hbf → Munich Hbf (~584 km)
    (
        "50.107147,8.663789",  # Frankfurt (Main) Hauptbahnhof
        "51.228189,6.769931",  # Düsseldorf Hauptbahnhof
    ),  # Frankfurt Hbf → Düsseldorf Hbf (~225 km)
    (
        "53.552809,9.979069",  # Hamburg Hauptbahnhof
        "51.056086,13.738101",  # Dresden Hauptbahnhof
    ),  # Hamburg Hbf → Dresden Hbf (~450 km)
    (
        "48.784013,9.176985",  # Stuttgart Hauptbahnhof
        "50.939227,6.957500",  # Köln Hauptbahnhof
    ),  # Stuttgart Hbf → Cologne Hbf (~350 km)
    (
        "51.314959,9.497554",  # Kassel-Wilhelmshöhe
        "49.412497,8.694605",  # Heidelberg Hauptbahnhof
    ),  # Kassel-Wilhelmshöhe → Heidelberg Hbf (~200 km)
    (
        "51.228189,6.769931",  # Düsseldorf Hauptbahnhof
        "50.939227,6.957500",  # Köln Hauptbahnhof
    ),  # Düsseldorf Hbf → Cologne Hbf (~40 km)
    (
        "50.939227,6.957500",  # Köln Hauptbahnhof
        "51.314959,9.497554",  # Kassel-Wilhelmshöhe
    ),  # Cologne Hbf → Kassel-Wilhelmshöhe (~250 km)
    (
        "48.140228,11.558330",  # München Hauptbahnhof
        "50.107147,8.663789",  # Frankfurt (Main) Hauptbahnhof
    ),  # Munich Hbf → Frankfurt Hbf (~400 km)
    (
        "52.376822,9.734188",  # Hannover Hauptbahnhof
        "53.552809,9.979069",  # Hamburg Hauptbahnhof
    ),  # Hannover Hbf → Hamburg Hbf (~150 km)
    (
        "49.412497,8.694605",  # Heidelberg Hauptbahnhof
        "48.784013,9.176985",  # Stuttgart Hauptbahnhof
    ),  # Heidelberg Hbf → Stuttgart Hbf (~120 km)
    (
        "51.056086,13.738101",  # Dresden Hauptbahnhof
        "50.107147,8.663789",  # Frankfurt (Main) Hauptbahnhof
    ),  # Dresden Hbf → Frankfurt Hbf (~400 km)
    (
        "54.322978,10.134988",  # Kiel Hauptbahnhof
        "50.731776,7.100913",  # Bonn Hauptbahnhof
    ),  # Kiel Hbf → Bonn Hbf (~500 km)
    (
        "49.451877,11.077209",  # Nürnberg Hauptbahnhof
        "53.078345,8.807817",  # Bremen Hauptbahnhof
    ),  # Nuremberg Hbf → Bremen Hbf (~520 km)
    (
        "47.570258,10.738361",  # Füssen Bahnhof
        "48.998495,12.091007",  # Regensburg Hauptbahnhof
    ),  # Füssen Bahnhof → Regensburg Hbf (~220 km)
    (
        "53.868778,11.144882",  # Wismar Hauptbahnhof
        "51.341147,12.378772",  # Leipzig Hauptbahnhof
    ),  # Wismar Hbf → Leipzig Hbf (~340 km)
    (
        "48.399587,9.992686",  # Ulm Hauptbahnhof
        "49.792501,9.929856",  # Würzburg Hauptbahnhof
    ),  # Ulm Hbf → Würzburg Hbf (~170 km)
    (
        "52.264259,10.536901",  # Braunschweig Hauptbahnhof
        "51.482084,11.970228",  # Halle (Saale) Hauptbahnhof
    ),  # Braunschweig Hbf → Halle (Saale) Hbf (~150 km)
    (
        "50.980424,11.328766",  # Erfurt Hauptbahnhof
        "49.231908,7.009366",  # Saarbrücken Hauptbahnhof
    ),  # Weimar Hbf → Saarbrücken Hbf (~370 km)
    (
        "53.865912,8.601556",  # Cuxhaven Bahnhof
        "51.536968,9.916897",  # Göttingen Hauptbahnhof
    ),  # Cuxhaven Bahnhof → Göttingen Hbf (~340 km)
    (
        "49.488057,8.468205",  # Mannheim Hauptbahnhof
        "54.089887,12.138891",  # Rostock Hauptbahnhof
    ),  # Mannheim Hbf → Rostock Hbf (~660 km)
    (
        "52.475994,13.365248",  # Berlin Südkreuz
        "52.756209,13.250556",  # Oranienburg Bahnhof
    ),  # Berlin Südkreuz → Oranienburg Bahnhof (~35 km)
    (
        "51.514339,7.464731",  # Dortmund Hauptbahnhof
        "51.534241,7.690185",  # Unna Bahnhof
    ),  # Dortmund Hbf → Unna Bahnhof (~25 km)
    (
        "52.525592,13.369545",  # Berlin Hauptbahnhof
        "52.376822,9.734188",  # Hannover Hauptbahnhof
    ),  # Berlin Hbf → Hannover Hbf (~280 km)
    (
        "50.107147,8.663789",  # Frankfurt (Main) Hauptbahnhof
        "48.784013,9.176985",  # Stuttgart Hauptbahnhof
    ),  # Frankfurt Hbf → Stuttgart Hbf (~200 km)
    (
        "53.552809,9.979069",  # Hamburg Hauptbahnhof
        "52.525592,13.369545",  # Berlin Hauptbahnhof
    ),  # Hamburg Hbf → Berlin Hbf (~280 km)
    (
        "51.314959,9.497554",  # Kassel-Wilhelmshöhe
        "50.076823,8.232704",  # Wiesbaden Hauptbahnhof
    ),  # Kassel-Wilhelmshöhe → Wiesbaden Hbf (~190 km)
    (
        "47.570258,10.738361",  # Füssen Bahnhof
        "47.551676,10.725907",  # Pfronten-Ried (train station)
    ),  # Füssen Bahnhof → Pfronten-Ried (~20 km)
    (
        "52.525592,13.369545",  # Berlin Hauptbahnhof
        "52.392095,13.06447",  # Potsdam Hauptbahnhof
    ),  # Berlin Hbf → Potsdam Hbf (~27 km)
    (
        "52.525592,13.369545",  # Berlin Hauptbahnhof
        "52.393174,13.526760",  # Königs Wusterhausen Bahnhof
    ),  # Berlin Hbf → Königs Wusterhausen Bahnhof (~35 km)
    (
        "48.140228,11.558330",  # München Hauptbahnhof
        "48.243644,11.890691",  # Erding Bahnhof
    ),  # Munich Hbf → Erding Bahnhof (~36 km)
    (
        "48.140228,11.558330",  # München Hauptbahnhof
        "47.999650,11.341490",  # Starnberg Bahnhof
    ),  # Munich Hbf → Starnberg Bahnhof (~26 km)
    (
        "51.228189,6.769931",  # Düsseldorf Hauptbahnhof
        "51.259972,7.151756",  # Wuppertal Hauptbahnhof
    ),  # Düsseldorf Hbf → Wuppertal Hbf (~31 km)
    (
        "50.939227,6.957500",  # Köln Hauptbahnhof
        "51.026410,7.564470",  # Gummersbach Bahnhof
    ),  # Cologne Hbf → Gummersbach Bahnhof (~55 km)
    (
        "50.107147,8.663789",  # Frankfurt (Main) Hauptbahnhof
        "50.076823,8.232704",  # Wiesbaden Hauptbahnhof
    ),  # Frankfurt Hbf → Wiesbaden Hbf (~33 km)
    (
        "50.107147,8.663789",  # Frankfurt (Main) Hauptbahnhof
        "50.001607,8.271101",  # Mainz Hauptbahnhof
    ),  # Frankfurt Hbf → Mainz Hbf (~35 km)
    (
        "50.107147,8.663789",  # Frankfurt (Main) Hauptbahnhof
        "49.985958,8.441499",  # Rüsselsheim Bahnhof
    ),  # Frankfurt Hbf → Rüsselsheim Bahnhof (~25 km)
    (
        "48.784013,9.176985",  # Stuttgart Hauptbahnhof
        "48.692226,9.014605",  # Böblingen Bahnhof
    ),  # Stuttgart Hbf → Böblingen Bahnhof (~20 km)
    (
        "50.980424,11.328766",  # Erfurt Hauptbahnhof
        "50.950791,10.702758",  # Gotha Hauptbahnhof
    ),  # Erfurt Hbf → Gotha Hbf (~40 km)
    (
        "53.552809,9.979069",  # Hamburg Hauptbahnhof
        "53.475653,9.704257",  # Buxtehude Bahnhof
    ),  # Hamburg Hbf → Buxtehude Bahnhof (~30 km)
]
