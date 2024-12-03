import os
import shutil


out_folder = 'submission_material/latex_sources'
fig_folder = 'figures'
main_file = 'main.tex'
bbl_file = 'main.bbl'
glossary_file = '0_glossary.tex'
glossary = {}
shortcuts = {}



class GlossaryEntry:
    def __init__(self, key):
        self.used = False
        self.first = None
        self.short = None
        self.short_plural = None
        self.long = None
        self.long_plural = None

    def s(self, plural=False):
        if not self.used:
            return self.s_first(plural)
        else:
            return self.s_short(plural)

    def s_first(self, plural=False):
        self.used = True
        if self.first is None:
            return f'{self.s_long(plural)} ({self.s_short(plural)})'
        elif self.first == 'short':
            return self.s_short(plural)
        elif self.first == 'long':
            return self.s_long(plural)

    def s_short(self, plural=False):
        self.used = True
        if plural and self.short_plural is not None:
            return self.short_plural
        return self.short + plural * 's'

    def s_long(self, plural=False):
        self.used = True
        if plural and self.long_plural is not None:
            return self.long_plural
        return self.long + plural * 's'


def glossary_dict(path):
    global glossary, shortcuts

    with open(path, 'r') as infile:
        lines = infile.readlines()

    for l in lines:
        if '\\DeclareAcronym' in l:
            key = l.split('{')[1].split('}')[0]
            glossary[key] = GlossaryEntry(key)
        elif 'short = ' in l:
            glossary[key].short = l.split(' = ')[1].split(',')[0]
        elif 'long = ' in l:
            glossary[key].long = l.split(' = ')[1].split(',')[0].split('\n')[0]
        elif 'first-style = short' in l:
            glossary[key].first = 'short'
        elif 'first-style = long' in l:
            glossary[key].first = 'long'
        elif 'long-plural-form' in l:
            glossary[key].long_plural = l.split(' = ')[1].split(',')[0].split('\n')[0]
        elif 'short-plural-form' in l:
            glossary[key].short_plural = l.split(' = ')[1].split(',')[0].split('\n')[0]
        elif '\\newcommand{' in l:
            key = l.split('{')[1].split('}')[0]
            val = (l.split('{')[2] + '{' + l.split('{')[3]).split('}')[0] + '}'
            shortcuts[key] = val

    for key in glossary.keys():
        glossary[key].short = expand_line(glossary[key].short)
        glossary[key].long = expand_line(glossary[key].long)

    for key in glossary.keys():
        glossary[key].used = False


def expand_line(l):
    global glossary, shortcuts

    if len(l) == 1:
        return l
    if l.split()[0].startswith('%'):
        return ''

    if '\\acresetall' in l:
        for key in glossary.keys():
            glossary[key].used = False
        return ''

    for key in shortcuts.keys():
        if key in l.replace('-', ' ').replace(',', ' ').replace('.', ' ').replace('~', ' ').replace('\'', ' ').replace('(', ' ').replace(')', ' ').split():
            l = l.replace(key, shortcuts[key])

    nb_ac = l.count('\\ac')
    for i in range(nb_ac):
        start = l.find('\\ac')
        command = l[start:].split('{')[0]
        key = l[start+len(command)+1:].split('}')[0]
        if command == '\\ac':
            expanded = glossary[key].s()
        elif command == '\\acf':
            expanded = glossary[key].s_first()
        elif command == '\\acs':
            expanded = glossary[key].s_short()
        elif command == '\\acl':
            expanded = glossary[key].s_long()
        elif command == '\\acp':
            expanded = glossary[key].s(plural=True)
        elif command in ['\\acfp', '\\acpf']:
            expanded = glossary[key].s_first(plural=True)
        elif command in ['\\acsp', '\\acps']:
            expanded = glossary[key].s_short(plural=True)
        elif command in ['\\aclp', '\\acpl']:
            expanded = glossary[key].s_long(plural=True)
        l = l.replace(command +'{' + key + '}', expanded)
    return l


def expand_latex_rec(path):
    global glossary
    outlines = ''

    with open(path, 'r') as infile:
        lines = infile.readlines()

    for l in lines:
        if '\\input{' in l:
            input_path = l.split('{')[1].split('}')[0]
            if not input_path.endswith('.tex'):
                input_path += '.tex'
            if glossary_file in input_path:
                glossary_dict(input_path)
            else:
                outlines += expand_latex_rec(input_path) + '\n'
        elif '\\includegraphics' in l:
            figure_path = l.split('{')[1].split('}')[0]
            figure_path_pdf = figure_path.split('/')[-1].split('.')[0] + '.pdf'
            outlines += l.replace(figure_path, figure_path_pdf)
        elif '\\bibliography{' in l:
            outlines += expand_latex_rec(bbl_file) + '\n'
        else:
            outlines += expand_line(l)
    return outlines


if __name__ == '__main__':
    os.makedirs(out_folder, exist_ok=True)

    ## copy figures to outfolder
    pdfs = [f for f in os.listdir(fig_folder) if f.endswith('.pdf')]
    for f in pdfs:
        shutil.copy2(os.path.join(fig_folder, f), out_folder)

    ## copy bst and cls
    bst_cls = [f for f in os.listdir('.') if f.endswith('.bst') or f.endswith('.cls')]
    for f in bst_cls:
        shutil.copy2(f, out_folder)

    ## process main_file
    outlines = expand_latex_rec(main_file)

    ## write
    with open(os.path.join(out_folder, main_file), 'w') as outfile:
        outfile.write(outlines)
