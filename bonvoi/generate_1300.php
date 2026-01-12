<?php
// generate_1300.php
// Génère 1300 phrases uniques et crée un fichier phrases_1300.php contenant un array PHP prêt à inclure.

header('Content-Type: text/plain; charset=utf-8');

function normalize($s) {
    $s = mb_strtolower($s, 'UTF-8');
    // enlever accents pour éviter doublons proches
    $s = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $s);
    $s = preg_replace('/[^a-z0-9 ]+/', '', $s);
    $s = preg_replace('/\s+/', ' ', trim($s));
    return $s;
}

// ✅ Base (tu peux ajouter/enlever)
$debuts = array(
    "L'avenir appartient à ceux qui",
    "Le succès appartient à ceux qui",
    "La réussite sourit à ceux qui",
    "La victoire appartient à ceux qui",
    "La discipline appartient à ceux qui",
    "Les opportunités viennent à ceux qui",
    "Le progrès arrive quand",
    "Le changement commence quand",
    "La force se révèle quand",
    "La liberté se construit quand",
    "Les grandes choses arrivent quand",
    "Ton avenir s’éclaire quand",
    "Ton potentiel se révèle quand",
    "Ton niveau change quand",
    "Ta vie avance quand"
);

$milieux = array(
    "croient à la valeur de leurs rêves",
    "travaillent avec discipline",
    "refusent d'abandonner",
    "avancent malgré la peur",
    "restent fidèles à leur vision",
    "se relèvent après chaque chute",
    "apprennent de chaque échec",
    "osent agir sans attendre",
    "sortent de leur zone de confort",
    "font confiance au processus",
    "restent constants dans l'effort",
    "gardent la foi malgré les doutes",
    "continuent même quand c'est difficile",
    "transforment la douleur en force",
    "choisissent la constance plutôt que la facilité"
);

$fins = array(
    "chaque jour.",
    "sans jamais renoncer.",
    "malgré les obstacles.",
    "avec courage et discipline.",
    "quoi qu'il arrive.",
    "jusqu'au bout.",
    "sans perdre l’espoir.",
    "en silence, mais avec puissance.",
    "pas à pas.",
    "avec une mentalité de gagnant.",
    "avec détermination.",
    "avec patience et persévérance.",
    "en restant focus.",
    "en travaillant dur.",
    "avec une foi inébranlable."
);

// ✅ Templates fixes pour varier encore plus
$templates = array(
    "{d} {m} {f}",
    "{d} {m} {f}",
    "{d} {m}, {f}",
    "{d} {m} — {f}",
    "{d} {m} : {f}"
);

// Ajoute quelques citations “style classique” (comme ton exemple)
$seed_quotes = array(
    "L'avenir appartient à ceux qui croient à la valeur de leurs rêves.",
    "Le seul moyen de faire du bon travail est d'aimer ce que vous faites.",
    "N'attends pas que les opportunités viennent à toi, crée-les.",
    "Le succès, c'est d'aller d'échec en échec sans perdre son enthousiasme.",
    "Crois en toi-même et en tout ce que tu es. Il y a quelque chose en toi de plus grand que n'importe quel obstacle.",
    "Le plus grand risque est de ne prendre aucun risque.",
    "La seule limite à notre épanouissement de demain sera nos doutes d'aujourd'hui."
);

$target = 1300;
$phrases = array();

// Commence par les seed quotes (si < 1300)
foreach ($seed_quotes as $q) {
    $phrases[] = $q;
}

$seen = array();
foreach ($phrases as $q) {
    $seen[normalize($q)] = true;
}

// Génération jusqu’à 1300 uniques
$tries = 0;
$max_tries = 200000;

while (count($phrases) < $target && $tries < $max_tries) {
    $tries++;

    $d = $debuts[array_rand($debuts)];
    $m = $milieux[array_rand($milieux)];
    $f = $fins[array_rand($fins)];
    $tpl = $templates[array_rand($templates)];

    $phrase = str_replace(
        array("{d}", "{m}", "{f}"),
        array($d, $m, $f),
        $tpl
    );

    // Petite variation : parfois ajoute un mini boost après
    if (mt_rand(1, 100) <= 18) {
        $addons = array(
            "Ne lâche rien.",
            "Tu vas y arriver.",
            "Reste déterminé.",
            "Continue d’avancer.",
            "Ton moment arrive."
        );
        $phrase .= " " . $addons[array_rand($addons)];
    }

    // Assure un point final
    $phrase = rtrim($phrase);
    if (!preg_match('/[.!?]$/u', $phrase)) {
        $phrase .= ".";
    }

    $key = normalize($phrase);
    if (!isset($seen[$key])) {
        $seen[$key] = true;
        $phrases[] = $phrase;
    }
}

if (count($phrases) < $target) {
    echo "Impossible d'atteindre 1300 phrases uniques avec ce dictionnaire.\n";
    echo "Générées: " . count($phrases) . "\n";
    echo "Augmente debuts/milieux/fins.\n";
    exit;
}

// Écrit un fichier phrases_1300.php contenant un array PHP
$outFile = __DIR__ . DIRECTORY_SEPARATOR . "phrases_1300.php";
$export = "<?php\n\n// phrases_1300.php\n// Array de 1300 phrases de motivation\n\nreturn " . var_export($phrases, true) . ";\n";

file_put_contents($outFile, $export);

echo "✅ OK : " . count($phrases) . " phrases générées.\n";
echo "📄 Fichier créé : phrases_1300.php\n";
