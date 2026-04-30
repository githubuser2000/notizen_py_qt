from __future__ import annotations

from dataclasses import dataclass

# Generated from the active language table in Notizen.NET/Notizen/languages.vb
# and the lang_keys enum in Notizen.vb.  Kept as literals so the Python port
# does not need the original VB.NET sources at runtime.

LANGUAGE_NAMES: dict[str, str] = {
    "de": "Deutsch",
    "en": "English",
    "zh": "Chinese",
    "fr": "French",
    "es": "Spanish",
    "ru": "Russian",
}

_LANGUAGE_TO_LEGACY = {
    "de": "deutsch",
    "deutsch": "deutsch",
    "german": "deutsch",
    "en": "english",
    "eng": "english",
    "english": "english",
    "englisch": "english",
    "zh": "chinese",
    "cn": "chinese",
    "chinese": "chinese",
    "chinesisch": "chinese",
    "fr": "french",
    "french": "french",
    "français": "french",
    "francais": "french",
    "es": "spanish",
    "spanish": "spanish",
    "español": "spanish",
    "espanol": "spanish",
    "ru": "russian",
    "russian": "russian",
    "русский": "russian",
}

LEGACY_KEYS: tuple[str, ...] = ('Strip1_1',
 'Strip1_2',
 'Strip1_3',
 'Strip1_4',
 'Strip1_5',
 'Strip1_6',
 'Strip1_7',
 'Strip1_8',
 'Strip1_9',
 'Strip1_10',
 'Strip1_11',
 'Strip1_12',
 'Strip1_13',
 'Strip1_14',
 'Strip1_15',
 'Strip1_16',
 'Strip1_17',
 'Strip1_18',
 'Strip1_19',
 'Strip2_1',
 'Strip3_1',
 'Strip3_2',
 'Strip4_1',
 'Strip4_2',
 'Strip4_3',
 'e1',
 'e2',
 'e3',
 'e4',
 'kontext1',
 'kontext2',
 'kontext3',
 'kontext4',
 'kontext5',
 'kontext2_1',
 'kontext2_2',
 'kontext2_3',
 'kontext2_4',
 'kontext2_5',
 'etwa_loeschen',
 'ja',
 'nein',
 'info1',
 'info2',
 'info3',
 'suche1',
 'suche2',
 'suche3',
 'suche4',
 'suche5',
 'neu1',
 'neu2',
 'eeoff1',
 'eeoff2',
 'eeoff3',
 'saveA',
 'OK',
 'abbrechen',
 'kontext2_6',
 'kontext2_7',
 'kontext2_8',
 'font_regular',
 'font_bold',
 'font_italic',
 'font_underline',
 'font_strikeout',
 'font_bigger',
 'font_smaller',
 'unity_note',
 'Strip1_20',
 'Strip1_1_1',
 'Strip1_1_2',
 'fehler1',
 'fehler2',
 'strip1_21',
 'pass1',
 'pass2',
 'pass3',
 'passerror1',
 'passerror2',
 'password',
 'passwort_falsch',
 'passerror3',
 'pw_unten_info',
 'kontext6',
 'kontext7',
 'kontext8',
 'kontext9',
 'kontext10',
 'e5',
 'kontext2_9',
 'kontext2_10',
 'sicherungen',
 'autostart',
 'color',
 'passwort',
 'pfaddatei',
 'alxerror',
 'export',
 'exportrtf',
 'exporttxt',
 'exporttxt2',
 'nexxt',
 'under',
 'kontext11',
 'suche6',
 'suche7',
 'aboutinfotext',
 'feedback',
 'close',
 'send',
 'no_send',
 'char10minimum',
 'no_feedback_sent',
 'minautostart',
 'autosave',
 'seconds',
 'scroll')

LEGACY_TRANSLATIONS: dict[str, dict[str, str]] = {'Strip1_1': {'deutsch': '&Menü', 'english': '&Menu', 'chinese': '文件', 'french': 'Menu', 'spanish': 'Menú', 'russian': 'Меню'},
 'Strip1_2': {'deutsch': '&Neue Datei STRG+N',
              'english': '&New File   CTRL+N',
              'chinese': '新          CTRL+N',
              'french': 'Nouveau fichier Ctrl + N',
              'spanish': 'Nuevo archivo Ctrl + N',
              'russian': 'Новый файл Ctrl + N'},
 'Strip1_3': {'deutsch': '&Öffnen        STRG+O',
              'english': '&Open        CTRL+O',
              'chinese': '打开        CTRL+O',
              'french': 'Ouvrir Ctrl + O',
              'spanish': 'Abrir Ctrl + O',
              'russian': 'Открыть CTRL + O'},
 'Strip1_4': {'deutsch': 'Speichern   STRG+S',
              'english': 'Save         CTRL+S',
              'chinese': '保存        CTRL+S',
              'french': 'Enregistrer CTRL + S',
              'spanish': 'Guardar Ctrl + S',
              'russian': 'Сохранить CTRL + S'},
 'Strip1_5': {'deutsch': 'Speichern &unter',
              'english': 'save &as',
              'chinese': '另存为',
              'french': 'Enregistrer sous',
              'spanish': 'guardar como',
              'russian': 'Сохранить как'},
 'Strip1_6': {'deutsch': 'Schließen', 'english': '&Close', 'chinese': '关闭', 'french': 'Fermer', 'spanish': 'Cerrar', 'russian': 'Закрыть'},
 'Strip1_7': {'deutsch': '&Einstellungen', 'english': '&Settings', 'chinese': '安装', 'french': 'Paramètres', 'spanish': 'Configuración', 'russian': 'Настройки'},
 'Strip1_8': {'deutsch': '&Beenden    STRG+Q',
              'english': '&Exit       CTRL+Q',
              'chinese': '结束        CTRL+Q',
              'french': 'Quitter Ctrl + Q',
              'spanish': 'Salir Ctrl + Q',
              'russian': 'Выйти Ctrl + Q'},
 'Strip1_9': {'deutsch': '&Hilfe', 'english': '&Help', 'chinese': '帮助', 'french': 'Aide', 'spanish': 'Ayuda', 'russian': 'Помощь'},
 'Strip1_10': {'deutsch': 'fuer den Programmierer hoffentlich',
               'english': 'for the programmer, I hope so',
               'chinese': '希望如此',
               'french': "pour le programmeur, je l'espère» ",
               'spanish': 'para el programador, así lo espero',
               'russian': 'для программиста, я надеюсь на это'},
 'Strip1_11': {'deutsch': 'Neue Datei', 'english': 'new file', 'chinese': '开始', 'french': 'nouveau fichier', 'spanish': 'archivo', 'russian': 'новый файл'},
 'Strip1_12': {'deutsch': 'Öffnen', 'english': 'open', 'chinese': '打开', 'french': 'ouvert', 'spanish': 'abierta', 'russian': 'открыть'},
 'Strip1_13': {'deutsch': 'Speichern ', 'english': 'save', 'chinese': '保存', 'french': 'sauver', 'spanish': 'guardar', 'russian': 'Сохранить'},
 'Strip1_14': {'deutsch': 'Schließen', 'english': 'close', 'chinese': '关闭', 'french': 'close', 'spanish': 'cerca', 'russian': 'Закрыть'},
 'Strip1_15': {'deutsch': 'Drucken', 'english': 'print', 'chinese': '打印', 'french': 'print', 'spanish': 'print', 'russian': 'Печать'},
 'Strip1_16': {'deutsch': 'Schrift', 'english': 'font', 'chinese': '字体', 'french': 'font', 'spanish': 'font', 'russian': 'Шрифт'},
 'Strip1_17': {'deutsch': 'Bearbeiten', 'english': 'change', 'chinese': '修改', 'french': 'changement', 'spanish': 'cambio', 'russian': 'Смена'},
 'Strip1_18': {'deutsch': 'Neu/Entf.',
               'english': 'new/remove',
               'chinese': '新的/移动',
               'french': 'new / Supprimer',
               'spanish': 'nuevo / eliminar',
               'russian': 'новый / удалить'},
 'Strip1_19': {'deutsch': 'Werkzeug-Streifen',
               'english': 'toolstrips',
               'chinese': '工具条',
               'french': 'toolstrips',
               'spanish': 'toolstrips',
               'russian': 'toolstrips'},
 'Strip2_1': {'deutsch': 'Schrift', 'english': 'font', 'chinese': '字体', 'french': 'font', 'spanish': 'font', 'russian': 'Шрифт'},
 'Strip3_1': {'deutsch': 'Neues Element',
              'english': 'new element',
              'chinese': '新要素',
              'french': 'nouvel élément',
              'spanish': 'nuevo elemento',
              'russian': 'новых элементов'},
 'Strip3_2': {'deutsch': 'Element löschen',
              'english': 'remove element',
              'chinese': '移动新要素',
              'french': "Retirer l'élément",
              'spanish': 'eliminar elemento',
              'russian': 'Удалить элемент'},
 'Strip4_1': {'deutsch': 'Aussschneiden STRG+X',
              'english': 'cut CTRL+X',
              'chinese': '剪切 CTRL++X',
              'french': 'Couper Ctrl + X',
              'spanish': 'Cortar Ctrl + X',
              'russian': 'Вырезать Ctrl + X'},
 'Strip4_2': {'deutsch': 'Kopieren STRG+C',
              'english': 'copy CTRL+C',
              'chinese': '复制 CTRL+C',
              'french': 'Copier Ctrl + C',
              'spanish': 'Copiar Ctrl + C',
              'russian': 'Копировать Ctrl + C'},
 'Strip4_3': {'deutsch': 'Einfügen STRG+V',
              'english': 'paste CTRL+V',
              'chinese': '粘贴 CTRL+V',
              'french': 'Coller Ctrl + V',
              'spanish': 'Pegar Ctrl + V',
              'russian': 'Вставить Ctrl + V'},
 'e1': {'deutsch': 'Einstellungen', 'english': 'settings', 'chinese': '安装', 'french': 'Paramètres', 'spanish': 'Configuración', 'russian': 'Настройки'},
 'e2': {'deutsch': 'In Deskbar zeigen',
        'english': 'show in Deskbar',
        'chinese': '桌面',
        'french': 'Afficher dans la barre de Bureau',
        'spanish': 'Mostrar en la barra del escritorio',
        'russian': 'сделали видимыми на панели задач'},
 'e3': {'deutsch': 'Sprache', 'english': 'language', 'chinese': '语言', 'french': 'language', 'spanish': 'idioma', 'russian': 'язык'},
 'e4': {'deutsch': 'ok', 'english': 'ok', 'chinese': 'ok', 'french': 'ok', 'spanish': 'ok', 'russian': 'OK'},
 'kontext1': {'deutsch': 'Kopieren', 'english': 'copy', 'chinese': '复制', 'french': 'Copier', 'spanish': 'copia', 'russian': 'Копировать'},
 'kontext2': {'deutsch': 'Ausschneiden', 'english': 'cut', 'chinese': '剪切', 'french': 'Couper', 'spanish': 'corte', 'russian': 'Вырезать'},
 'kontext3': {'deutsch': 'Einfuegen', 'english': 'paste', 'chinese': '粘贴', 'french': 'coller', 'spanish': 'Pegar', 'russian': 'Вставить'},
 'kontext4': {'deutsch': 'Löschen', 'english': 'delete', 'chinese': '删除', 'french': 'supprimer', 'spanish': 'borrar', 'russian': 'Удалить'},
 'kontext5': {'deutsch': 'Suchen', 'english': 'search', 'chinese': '搜索', 'french': 'Recherche', 'spanish': 'Buscar', 'russian': 'Поиск'},
 'kontext2_1': {'deutsch': 'Neu darunter [einfg]',
                'english': 'new under [ins]',
                'chinese': '新的',
                'french': 'Recherche',
                'spanish': 'Buscar',
                'russian': 'Поиск'},
 'kontext2_2': {'deutsch': 'Umbenennen ',
                'english': 'rename',
                'chinese': '重命名',
                'french': 'Nouveau sous [Ins]',
                'spanish': 'nuevo bajo [INS]',
                'russian': 'под новым [Ins]'},
 'kontext2_3': {'deutsch': 'Löschen [entf]',
                'english': 'remove [del]',
                'chinese': '移动',
                'french': 'Renommer',
                'spanish': 'Renombrar',
                'russian': 'Переименовать'},
 'kontext2_4': {'deutsch': 'Speichern',
                'english': 'save',
                'chinese': '保存',
                'french': 'supprimer [Suppr]',
                'spanish': 'eliminar [del]',
                'russian': 'Удалить [деле]'},
 'kontext2_5': {'deutsch': 'Desktop-Notiz', 'english': 'desk note', 'chinese': '新窗口', 'french': 'save', 'spanish': 'guardar', 'russian': 'Сохранить'},
 'etwa_loeschen': {'deutsch': 'Möchten Sie den Knoten wirklich löschen?',
                   'english': 'Do you want to remove this node?',
                   'chinese': '是否移动此节点？',
                   'french': 'note desk',
                   'spanish': 'nota de escritorio',
                   'russian': 'столе записки'},
 'ja': {'deutsch': 'Ja',
        'english': 'Yes',
        'chinese': '是',
        'french': 'Voulez-vous supprimer ce noeud?',
        'spanish': '¿Desea eliminar este nodo?',
        'russian': 'Вы хотите удалить этот узел?'},
 'nein': {'deutsch': 'Nein', 'english': 'No', 'chinese': '否', 'french': 'Oui', 'spanish': 'Sí', 'russian': 'Да'},
 'info1': {'deutsch': 'Baum in dem die Notizen geordnet sind', 'english': 'notes tree', 'chinese': '词条正确', 'french': 'Non', 'spanish': 'No', 'russian': 'Нет'},
 'info2': {'deutsch': 'Anzeige der jeweiligen Notiz',
           'english': 'place where Notes are shown',
           'chinese': '显示节点所在位置',
           'french': 'Notes arbre',
           'spanish': 'toma nota de árbol',
           'russian': 'отмечает, дерево'},
 'info3': {'deutsch': 'Zeigen/Ausblenden',
           'english': 'Show/Hide',
           'chinese': '显示/隐藏',
           'french': 'lieu où les notes sont affichées',
           'spanish': 'lugar donde se muestran Notas',
           'russian': 'место, где показаны Заметки'},
 'suche1': {'deutsch': 'Suche',
            'english': 'search',
            'chinese': '搜索',
            'french': 'Afficher / Masquer',
            'spanish': 'Mostrar / Ocultar',
            'russian': 'Показать / Скрыть'},
 'suche2': {'deutsch': 'Suchen', 'english': 'search', 'chinese': '搜索', 'french': 'Recherche', 'spanish': 'Buscar', 'russian': 'Поиск'},
 'suche3': {'deutsch': 'Fertig', 'english': 'back', 'chinese': '完成', 'french': 'Retour', 'spanish': 'Volver', 'russian': 'Назад'},
 'suche4': {'deutsch': 'Alle Knoten durchsuchen?',
            'english': 'search all nodes?',
            'chinese': '搜索所有词条？',
            'french': 'rechercher tous les nœuds? ',
            'spanish': 'buscar todos los nodos?',
            'russian': 'Поиск Всех узлов'},
 'suche5': {'deutsch': 'Ergebnisse:', 'english': 'results:', 'chinese': '结果', 'french': 'Results:', 'spanish': 'resultados', 'russian': 'Результат:'},
 'neu1': {'deutsch': 'Wollen Sie vorher speichern?',
          'english': 'Do you want to save before?',
          'chinese': '是否将前面保存？',
          'french': 'Voulez-vous enregistrer avant?',
          'spanish': '¿Desea guardar antes?',
          'russian': 'Вы хотите сначала сохранить? '},
 'neu2': {'deutsch': 'von vorn beginnen',
          'english': 'begin again',
          'chinese': '重新开始',
          'french': 'recommencer',
          'spanish': 'empezar de nuevo',
          'russian': 'начинать'},
 'eeoff1': {'deutsch': 'von vorn beginnen',
            'english': 'begin again',
            'chinese': '重新开始',
            'french': 'recommencer',
            'spanish': 'empezar de nuevo',
            'russian': 'начинать'},
 'eeoff2': {'deutsch': 'Vorhandene Daten werden gelöscht.',
            'english': 'Data will be lost.',
            'chinese': '消除日期',
            'french': 'Les données seront perdues.',
            'spanish': 'Los datos se perderán.',
            'russian': 'Данные будут потеряны.'},
 'eeoff3': {'deutsch': 'Sind sie sicher, dass Sie vorn beginnen wollen?',
            'english': 'Are you sure to begin again?',
            'chinese': '是否决定重新开始?',
            'french': 'Etes-vous sûr de vouloir recommencer?',
            'spanish': '¿Estás seguro de volver a empezar?',
            'russian': 'Вы уверены, что хотите начать заново?'},
 'saveA': {'deutsch': 'Möchten Sie vorher speichern?',
           'english': 'Do you want to save before?',
           'chinese': '是否将前面保存？',
           'french': 'Voulez-vous enregistrer avant?',
           'spanish': '¿Desea guardar antes?',
           'russian': 'Вы хотите сначала сохранить? '},
 'OK': {'deutsch': 'OK', 'english': 'OK', 'chinese': 'OK', 'french': 'OK', 'spanish': 'OK', 'russian': 'OK'},
 'abbrechen': {'deutsch': 'abbrechen', 'english': 'cancel', 'chinese': '中止', 'french': 'Annuler', 'spanish': 'cancelar', 'russian': 'Отмена'},
 'kontext2_6': {'deutsch': 'Kopieren', 'english': 'copy', 'chinese': '复制', 'french': 'Copier', 'spanish': 'copia', 'russian': 'Копировать'},
 'kontext2_7': {'deutsch': 'Ausschneiden', 'english': 'cut', 'chinese': '剪切', 'french': 'Couper', 'spanish': 'corte', 'russian': 'Вырезать'},
 'kontext2_8': {'deutsch': 'Einfügen', 'english': 'paste', 'chinese': '粘贴', 'french': 'coller', 'spanish': 'Pegar', 'russian': 'Вставить'},
 'font_regular': {'deutsch': 'normale Schrift',
                  'english': 'regular font',
                  'chinese': '常规字体',
                  'french': 'font régulièrement',
                  'spanish': 'fuente regular',
                  'russian': 'Обычный шрифт'},
 'font_bold': {'deutsch': 'Fett-Schrift', 'english': 'bold font', 'chinese': '黑体', 'french': 'font bold', 'spanish': 'negrita', 'russian': 'Жирный шрифт'},
 'font_italic': {'deutsch': 'Kursiv-Schrift', 'english': 'italic font', 'chinese': '斜体', 'french': 'italique', 'spanish': 'cursiva', 'russian': 'Курсив'},
 'font_underline': {'deutsch': 'unterstrichen',
                    'english': 'underline',
                    'chinese': '强调',
                    'french': 'underline',
                    'spanish': 'subrayado',
                    'russian': 'Подчеркнутый'},
 'font_strikeout': {'deutsch': 'durchgestrichen', 'english': 'strikeout', 'chinese': '划去', 'french': 'barrées', 'spanish': 'tachado', 'russian': 'Зачеркнутый'},
 'font_bigger': {'deutsch': 'grössere Schrift',
                 'english': 'bigger font',
                 'chinese': '大字体',
                 'french': 'font plus grands',
                 'spanish': 'fuente mayor',
                 'russian': 'Большой шрифт'},
 'font_smaller': {'deutsch': 'kleinere Schrift',
                  'english': 'smaller font',
                  'chinese': '小字体',
                  'french': 'petits caractères',
                  'spanish': 'fuente más pequeña',
                  'russian': 'Мелкий шрифт'},
 'unity_note': {'deutsch': 'Zusammenfassen',
                'english': 'together in one node',
                'chinese': '一起，在一个节点',
                'french': 'ensemble dans un noeud',
                'spanish': 'juntos en un nodo',
                'russian': 'вместе в один узел'},
 'Strip1_20': {'deutsch': 'Info + Hilfe + Feedback',
               'english': 'info + help + feedback',
               'chinese': '信息+帮助+反馈',
               'french': 'info + aide + feedback» ',
               'spanish': 'info + ayuda + de votos',
               'russian': 'Инфо + + Помощь Обратная связь'},
 'Strip1_1_1': {'deutsch': 'alles', 'english': 'everything', 'chinese': '一切', 'french': 'tout', 'spanish': 'todo', 'russian': 'все'},
 'Strip1_1_2': {'deutsch': 'unterhalb des markierten Knotens',
                'english': 'inside the marked node',
                'chinese': '内的标记节点',
                'french': "à l'intérieur du nœud marqué",
                'spanish': 'dentro del nodo marcado',
                'russian': 'ниже отмечены узлы'},
 'fehler1': {'deutsch': 'Keine Datei wurde geladen.',
             'english': 'No file is loaded.',
             'chinese': '没有文件被加载。',
             'french': "Aucun fichier n'est chargé.",
             'spanish': 'No existe el fichero está cargado.',
             'russian': 'Не был загружен файл'},
 'fehler2': {'deutsch': 'Fehler beim Laden von XML Code:',
             'english': 'Error when loading xml code:',
             'chinese': '错误时加载XML代码:',
             'french': 'Erreur lors du chargement de code XML:',
             'spanish': 'Error al cargar el código XML:',
             'russian': 'Ошибка при загрузке XML-код:'},
 'strip1_21': {'deutsch': 'Passwort setzen',
               'english': 'set password',
               'chinese': '设置密码',
               'french': 'Mot de code',
               'spanish': 'Set Password',
               'russian': 'Установить пароль'},
 'pass1': {'deutsch': 'altes Passwort',
           'english': 'old password',
           'chinese': '旧密码',
           'french': 'ancien mot de passe',
           'spanish': 'contraseña antigua',
           'russian': 'Старый пароль'},
 'pass2': {'deutsch': 'neues Passwort',
           'english': 'new password',
           'chinese': '新密码',
           'french': 'nouveau mot de passe',
           'spanish': 'nueva contraseña',
           'russian': 'Новый пароль'},
 'pass3': {'deutsch': 'wiederholen', 'english': 'again', 'chinese': '再次', 'french': 'à nouveau', 'spanish': 'nuevo', 'russian': 'еще раз'},
 'passerror1': {'deutsch': 'Das Passwort darf nicht mehr als 24 Zeichen haben.',
                'english': 'Not more than 24 characters are allowed.',
                'chinese': '不超过24个字符是允许的。',
                'french': 'caractères Pas plus de 24 ans sont autorisées.',
                'spanish': '(personajes No más de 24 están permitidas.)',
                'russian': 'Допускается Не более 24 символов.'},
 'passerror2': {'deutsch': 'Das alte Passwort ist falsch.',
                'english': 'The old password is wrong.',
                'chinese': '旧密码是错误的。',
                'french': "L'ancien mot de passe est erroné.",
                'spanish': 'La contraseña antigua es incorrecta.',
                'russian': 'старый пароль неправильный.'},
 'password': {'deutsch': 'Passwort', 'english': 'password', 'chinese': '密码', 'french': 'password', 'spanish': 'contraseña', 'russian': 'пароль'},
 'passwort_falsch': {'deutsch': 'Passwort falsch oder Datei fehlerhaft',
                     'english': 'wrong password or incorrect file',
                     'chinese': '错误的密码或不正确的文件',
                     'french': 'mauvais mot de passe ou un fichier incorrect',
                     'spanish': 'contraseña equivocada o incorrecta de archivo',
                     'russian': 'неправильный пароль или неправильный файл'},
 'passerror3': {'deutsch': 'Die letzten beiden Eingaben sind nicht gleich.',
                'english': 'The last 3 entrys are not equal.',
                'chinese': '最后的3项不相等。',
                'french': 'Les 3 dernières Entrys ne sont pas égaux.',
                'spanish': 'Los 3 últimos Juegos PSP no son iguales.',
                'russian': 'последние 3 символа не одинаковы.'},
 'pw_unten_info': {'deutsch': 'Leeres Feld bedeutet kein Passwort.',
                   'english': 'Empty textbox means no password.',
                   'chinese': '空文本就没有密码。',
                   'french': "zone de texte vide signifie qu'aucun mot de passe.",
                   'spanish': 'texto vacío significa que no hay contraseña.',
                   'russian': 'Пусто текстовое средствами без пароля.'},
 'kontext6': {'deutsch': 'Bild einfügen',
              'english': 'insert picture',
              'chinese': '插入图片',
              'french': 'Insérer image',
              'spanish': 'Insertar imagen',
              'russian': 'вставить картинку'},
 'kontext7': {'deutsch': 'Datum einfügen',
              'english': 'insert date',
              'chinese': '插入日期',
              'french': 'insérer la date',
              'spanish': 'insertar fecha',
              'russian': 'Дата'},
 'kontext8': {'deutsch': 'Hintergrundfarbe',
              'english': 'background color',
              'chinese': '背景颜色',
              'french': 'couleur de fond',
              'spanish': 'color de fondo',
              'russian': 'Цвет фона'},
 'kontext9': {'deutsch': 'Minimieren', 'english': 'minimize', 'chinese': '最小化', 'french': 'Minimize', 'spanish': 'minimizar', 'russian': 'Свернуть'},
 'kontext10': {'deutsch': 'Schließen', 'english': 'close', 'chinese': '关闭', 'french': 'close', 'spanish': 'cerca', 'russian': 'Закрыть'},
 'e5': {'deutsch': 'Desktop-Notitz-Fensterrand einblenden',
        'english': 'show desknote borders',
        'chinese': '显示办公桌边界',
        'french': 'Afficher les frontières desknote',
        'spanish': 'Mostrar las fronteras Desknote',
        'russian': 'Показать границы Desknote'},
 'kontext2_9': {'deutsch': 'Hintergrundfarbe',
                'english': 'Background Color',
                'chinese': '背景颜色',
                'french': 'Couleur de fond',
                'spanish': 'Color de fondo',
                'russian': 'Цвет фона'},
 'kontext2_10': {'deutsch': 'Schriftfarbe',
                 'english': 'Font Color',
                 'chinese': '字体颜色',
                 'french': 'Font Color',
                 'spanish': 'Color de fuente',
                 'russian': 'Цвет шрифта'},
 'sicherungen': {'deutsch': 'Sicherungen',
                 'english': 'backup copies',
                 'chinese': '备份',
                 'french': 'copies de sauvegarde',
                 'spanish': 'copias de seguridad',
                 'russian': 'резервные копии'},
 'autostart': {'deutsch': 'Autostart', 'english': 'autorun', 'chinese': '自动运行', 'french': 'autorun', 'spanish': 'autorun', 'russian': 'автозапуск'},
 'color': {'deutsch': 'Farbe', 'english': 'color', 'chinese': '颜色', 'french': 'color', 'spanish': 'color', 'russian': 'Цвет'},
 'passwort': {'deutsch': 'Passwort', 'english': 'password', 'chinese': '密码', 'french': 'password', 'spanish': 'contraseña', 'russian': 'пароль'},
 'pfaddatei': {'deutsch': 'Pfad+Datei',
               'english': 'Path+File',
               'chinese': '路径+文件',
               'french': 'Path + File',
               'spanish': 'Ruta + Archivo',
               'russian': 'путь + Файл '},
 'alxerror': {'deutsch': 'Die Datei muss auf .alx enden!',
              'english': 'File has to end with .alx !',
              'chinese': '文件已经结束了。',
              'french': 'Le fichier a pour terminer. alx! ',
              'spanish': 'El archivo tiene que terminar con .alx',
              'russian': 'Файл должен заканчиваться на. ALX!'},
 'export': {'deutsch': 'Export', 'english': 'export', 'chinese': '出口', 'french': 'export', 'spanish': 'exportación', 'russian': 'экспорт'},
 'exportrtf': {'deutsch': 'in rtf', 'english': 'in rtf', 'chinese': '以RTF', 'french': 'dans le rtf', 'spanish': 'en rtf', 'russian': 'в RTF'},
 'exporttxt': {'deutsch': 'in ansi txt',
               'english': 'in ansi txt',
               'chinese': '在ANSI txt 的',
               'french': 'dans la norme ANSI txt',
               'spanish': 'en ANSI txt',
               'russian': 'В ANSI TXT'},
 'exporttxt2': {'deutsch': 'in unicode txt',
                'english': 'in unicode txt',
                'chinese': '在Unicode txt的',
                'french': 'IN TXT unicode',
                'spanish': 'en TXT Unicode',
                'russian': 'в Unicode TXT'},
 'nexxt': {'deutsch': 'daneben [Enter]',
           'english': 'next [Enter]',
           'chinese': '下一页[进入',
           'french': 'next [Entrée]',
           'spanish': 'Siguiente [Enter]',
           'russian': 'Следующий [Enter]'},
 'under': {'deutsch': 'darunter [einfg]',
           'english': 'under [insert]',
           'chinese': '在[插入]',
           'french': 'en vertu de [insérer]',
           'spanish': 'en [insertar]',
           'russian': 'под [вставить]'},
 'kontext11': {'deutsch': 'Neu daneben [Enter]',
               'english': 'new next [Enter]',
               'chinese': '新的未来[进入] ',
               'french': 'prochain nouveau sur [Entrée]',
               'spanish': 'nuevo siguiente [Enter]',
               'russian': 'новый следующий [Enter]'},
 'suche6': {'deutsch': 'ganze Wörter',
            'english': 'whole words',
            'chinese': '全字',
            'french': 'Mot entier',
            'spanish': 'palabras completas',
            'russian': 'Всего слов'},
 'suche7': {'deutsch': 'Groß-/Klein-Schreibung beachten',
            'english': 'case sensitive',
            'chinese': '区分大小写',
            'french': 'case sensitive',
            'spanish': 'asunto sensible',
            'russian': 'случае чувствительной'},
 'aboutinfotext': {'deutsch': '• Eine Desktop-Notitz erstellt man mit dem Menü eines Knotens und erreicht man dann über das Menü des Trayicons.\r\n'
                              '\r\n'
                              '• Einzelne Knoten lassen sich als rtf Datei zusammenfassen, die z.B. mit Wordpad lesbar sind.\r\n'
                              '\r\n'
                              '• Erstellt man eine Verknüpfung mit dem Ziel "C:\\Ort1\\notizen.exe" -min "C:\\Dokumente und Einstellungen\\Benutzer\\Eigene '
                              'Dateien\\Notizen\\datei.alx" also erst notizen.exe und die alx-Datei, dann öffnet sich das Programm zusammen mit der '
                              'Notizendatei. Beide Ortsangaben müssen am Besten in Anführungszeichen stehen. Stellt man diese Verknüpfung in den '
                              'Autostartordner, so hat man immer seine gut sortierten Notizen zur Hand.\r\n'
                              '\r\n'
                              '• Die Anhabe /min sorgt als Programmstartangabe z.B. in einer Verknüpfung für ein minimiertes Hauptfenster bei Beginn. '
                              '(notizen.exe /min Zieldatei)" \r\n'
                              '\r\n'
                              '• Startet man Notizen .Net mit Adminrechten kann danach eine alx-Datei durch den Explorerer erkannt werden.',
                   'english': '• A desknote can be created by using the menu of the node and can be reached by the trayicon menu.\r\n'
                              '\r\n'
                              '• Nodes can be summed up as rtf file, witch can be read with Wordpad, Word or OpenOffice.\r\n'
                              '\r\n'
                              '• Create a Link with with a destination: "C:\\Ort1\\notizen.exe" -min "C:\\Dokumente und Einstellungen\\Benutzer\\Eigene '
                              'Dateien\\Notizen\\datei.alx" , first notizen.exe and the alx file, the program will be opend by opening the File. Both '
                              'Locations should be better into double quotes. If you put the link into the autostart folder you have your notes by starting '
                              'the Computer.\r\n'
                              '\r\n'
                              '• The argument /min after notizen.exe, maybe in a line of a link, makes the programm running minimized at startup. (notizen.exe '
                              '/min destination file)" \r\n'
                              '\r\n'
                              '•If you run Notizen .Net with Administrator permissions once, the explorer will know Notizen .NET alx Files.',
                   'chinese': '• A desknote can be created by using the menu of the node and can be reached by the trayicon menu.\r\n'
                              '\r\n'
                              '• Nodes can be summed up as rtf file, witch can be read with Wordpad, Word or OpenOffice.\r\n'
                              '\r\n'
                              '• Create a Link with with a destination: "C:\\Ort1\\notizen.exe" -min "C:\\Dokumente und Einstellungen\\Benutzer\\Eigene '
                              'Dateien\\Notizen\\datei.alx" , first notizen.exe and the alx file, the program will be opend by opening the File. Both '
                              'Locations should be better into double quotes. If you put the link into the autostart folder you have your notes by starting '
                              'the Computer.\r\n'
                              '\r\n'
                              '• The argument /min after notizen.exe, maybe in a line of a link, makes the programm running minimized at startup. (notizen.exe '
                              '/min destination file)" \r\n'
                              '\r\n'
                              '•If you run Notizen .Net with Administrator permissions once, the explorer will know Notizen .NET alx Files.',
                   'french': '• A desknote can be created by using the menu of the node and can be reached by the trayicon menu.\r\n'
                             '\r\n'
                             '• Nodes can be summed up as rtf file, witch can be read with Wordpad, Word or OpenOffice.\r\n'
                             '\r\n'
                             '• Create a Link with with a destination: "C:\\Ort1\\notizen.exe" -min "C:\\Dokumente und Einstellungen\\Benutzer\\Eigene '
                             'Dateien\\Notizen\\datei.alx" , first notizen.exe and the alx file, the program will be opend by opening the File. Both Locations '
                             'should be better into double quotes. If you put the link into the autostart folder you have your notes by starting the '
                             'Computer.\r\n'
                             '\r\n'
                             '• The argument /min after notizen.exe, maybe in a line of a link, makes the programm running minimized at startup. (notizen.exe '
                             '/min destination file)" \r\n'
                             '\r\n'
                             '•If you run Notizen .Net with Administrator permissions once, the explorer will know Notizen .NET alx Files.',
                   'spanish': '• A desknote can be created by using the menu of the node and can be reached by the trayicon menu.\r\n'
                              '\r\n'
                              '• Nodes can be summed up as rtf file, witch can be read with Wordpad, Word or OpenOffice.\r\n'
                              '\r\n'
                              '• Create a Link with with a destination: "C:\\Ort1\\notizen.exe" -min "C:\\Dokumente und Einstellungen\\Benutzer\\Eigene '
                              'Dateien\\Notizen\\datei.alx" , first notizen.exe and the alx file, the program will be opend by opening the File. Both '
                              'Locations should be better into double quotes. If you put the link into the autostart folder you have your notes by starting '
                              'the Computer.\r\n'
                              '\r\n'
                              '• The argument /min after notizen.exe, maybe in a line of a link, makes the programm running minimized at startup. (notizen.exe '
                              '/min destination file)" \r\n'
                              '\r\n'
                              '•If you run Notizen .Net with Administrator permissions once, the explorer will know Notizen .NET alx Files.',
                   'russian': '• A desknote can be created by using the menu of the node and can be reached by the trayicon menu.\r\n'
                              '\r\n'
                              '• Nodes can be summed up as rtf file, witch can be read with Wordpad, Word or OpenOffice.\r\n'
                              '\r\n'
                              '• Create a Link with with a destination: "C:\\Ort1\\notizen.exe" -min "C:\\Dokumente und Einstellungen\\Benutzer\\Eigene '
                              'Dateien\\Notizen\\datei.alx" , first notizen.exe and the alx file, the program will be opend by opening the File. Both '
                              'Locations should be better into double quotes. If you put the link into the autostart folder you have your notes by starting '
                              'the Computer.\r\n'
                              '\r\n'
                              '• The argument /min after notizen.exe, maybe in a line of a link, makes the programm running minimized at startup. (notizen.exe '
                              '/min destination file)" \r\n'
                              '\r\n'
                              '•If you run Notizen .Net with Administrator permissions once, the explorer will know Notizen .NET alx Files.'},
 'feedback': {'deutsch': 'persönliche Meinung / Fehlermeldung / Feature-Vorschlag',
              'english': 'opinion / bug report / feature request',
              'chinese': '意见/错误报告/功能要求',
              'french': 'opinion / rapport de bug / demande de fonctionnalité',
              'spanish': 'opinión / informe de fallo / feature request',
              'russian': 'Мнение / сообщение об ошибке / Запрос функции'},
 'close': {'deutsch': 'schließen', 'english': 'close', 'chinese': '关闭', 'french': 'close', 'spanish': 'cerca', 'russian': 'Закрыть'},
 'send': {'deutsch': 'senden', 'english': 'send', 'chinese': '发送', 'french': 'Envoyer', 'spanish': 'Enviar', 'russian': 'Отправить'},
 'no_send': {'deutsch': 'Nach 3 Feebacks kann man erst wieder am nächsten Tag senden.',
             'english': 'After 3 Feedbacks sending feedback is only possible tomorrow.',
             'chinese': '3反馈后，发送反馈是唯一可能的明天。',
             'french': "Après 3 Feedbacks rétroaction d'envoi est seulement possible demain.",
             'spanish': 'Después de 3 Opiniones envío de comentarios sólo es posible mañana.',
             'russian': 'После 3 Отзывы отправка отзыва возможна только завтра.'},
 'char10minimum': {'deutsch': 'Geben sie mindestens 10 Zeichen ein!',
                   'english': 'A minimal input of 10 characters is requiered.',
                   'chinese': '10个字符最小输入需求列表。',
                   'french': 'Un apport minimal de 10 caractères est requiered. ',
                   'spanish': 'Una aportación mínima de 10 caracteres es Requiere.',
                   'russian': 'является минимальный ввод 10 символов.'},
 'no_feedback_sent': {'deutsch': 'Feedback konnte nicht gesendet werden.',
                      'english': 'Feedback was not transmitted.',
                      'chinese': '反馈不传染。',
                      'french': "évaluation n'a pas été transmise",
                      'spanish': 'votos no se transmite.',
                      'russian': 'обратной связи не было передано.'},
 'minautostart': {'deutsch': 'minimierter autostart',
                  'english': 'minimized autorun',
                  'chinese': '最小化自动运行',
                  'french': 'minimisées démarrage automatique',
                  'spanish': 'reducir al mínimo el arranque automático',
                  'russian': 'свести к минимуму автоматического запуска'},
 'autosave': {'deutsch': 'automatisches speichern jede',
              'english': 'automatic saves every',
              'chinese': '自动保存每个',
              'french': 'Sauvegarde automatique',
              'spanish': 'Automatic Save',
              'russian': 'автоматически сохранит каждый'},
 'seconds': {'deutsch': 'Sekunde', 'english': 'seconds', 'chinese': '秒', 'french': 'Seconds', 'spanish': 'Segundos', 'russian': 'секунда'},
 'scroll': {'deutsch': 'scroll', 'english': 'scroll', 'chinese': '滚动', 'french': 'défilement', 'spanish': 'desplazamiento', 'russian': 'прокрутки'}}


@dataclass(slots=True, frozen=True)
class TranslationEntry:
    key: str
    index: int
    text: str
    language: str

    def as_dict(self) -> dict[str, object]:
        return {"key": self.key, "index": self.index, "language": self.language, "text": self.text}


def normalize_language(value: str | None, *, default: str = "de") -> str:
    text = (value or default or "de").strip().lower().replace("_", "-")
    if not text or text == "auto":
        text = default
    text = text.split("-", 1)[0]
    legacy = _LANGUAGE_TO_LEGACY.get(text) or _LANGUAGE_TO_LEGACY.get((value or "").strip().lower())
    if legacy == "deutsch":
        return "de"
    if legacy == "english":
        return "en"
    if legacy == "chinese":
        return "zh"
    if legacy == "french":
        return "fr"
    if legacy == "spanish":
        return "es"
    if legacy == "russian":
        return "ru"
    return default


def legacy_language_key(language: str | None) -> str:
    code = normalize_language(language)
    return {"de": "deutsch", "en": "english", "zh": "chinese", "fr": "french", "es": "spanish", "ru": "russian"}[code]


def key_index(key: str | int) -> int:
    if isinstance(key, int):
        if 0 <= key < len(LEGACY_KEYS):
            return key
        raise KeyError(f"Sprachschlüsselindex außerhalb des Bereichs: {key}")
    text = (key or "").strip()
    if text.isdigit():
        return key_index(int(text))
    lowered = text.casefold()
    for index, name in enumerate(LEGACY_KEYS):
        if name.casefold() == lowered:
            return index
    raise KeyError(f"Unbekannter Sprachschlüssel: {key}")


def translate(key: str | int, language: str | None = "de", *, fallback: bool = True) -> str:
    index = key_index(key)
    key_name = LEGACY_KEYS[index]
    lang = legacy_language_key(language)
    value = LEGACY_TRANSLATIONS[key_name].get(lang, "")
    if value or not fallback:
        return value
    for fallback_lang in ("english", "deutsch"):
        value = LEGACY_TRANSLATIONS[key_name].get(fallback_lang, "")
        if value:
            return value
    return key_name


def iter_translations(language: str | None = "de", *, fallback: bool = True) -> list[TranslationEntry]:
    code = normalize_language(language)
    return [TranslationEntry(key=name, index=index, language=code, text=translate(index, code, fallback=fallback)) for index, name in enumerate(LEGACY_KEYS)]


def translation_table(*, languages: list[str] | None = None) -> list[dict[str, object]]:
    requested = languages or list(LANGUAGE_NAMES)
    normalized = [normalize_language(lang) for lang in requested]
    rows: list[dict[str, object]] = []
    for index, key in enumerate(LEGACY_KEYS):
        row: dict[str, object] = {"index": index, "key": key}
        for code in normalized:
            row[code] = translate(key, code)
        rows.append(row)
    return rows
