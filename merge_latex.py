import os
import shutil
from PIL import Image


out_folder = 'submission_material'
fig_folder = 'figures'
latex_main = 'main.tex'
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
    if not l.split() or l.split()[0].startswith('%'):
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
    output_lines = ''

    with open(path, 'r') as infile:
        lines = infile.readlines()

    for l in lines:
        if '\\input{' in l:
            input_path = l.split('{')[1].split('}')[0]
            if not input_path.endswith('.tex'):
                input_path += '.tex'
            if 'glossary' in input_path:
                glossary_dict(input_path)
            else:
                output_lines += expand_latex_rec(input_path) + '\n'
        elif '\\includegraphics' in l:
            figure_path = l.split('{')[1].split('}')[0]
            output_lines += l.replace(figure_path, figure_path.split('/')[-1].split('.')[0] + '.jpg')
        elif '\\bibliography{' in l:
            output_lines += expand_latex_rec('main.bbl') + '\n'
        else:
            output_lines += expand_line(l)
    return output_lines


def figures_jpg(dpi=200):
    ## convert image figures to jpg
    imgs = [os.path.join(fig_folder, f) for f in os.listdir(fig_folder) if f.endswith(('.png', 'jpg', 'jpeg'))]
    for f_img in imgs:
        img = Image.open(f_img).convert("RGB")
        img.save(os.path.join(
            out_folder,
            os.path.splitext(f_img)[0] + '.jpg'
        ))

    ## convert pdfs figures to jpg
    pdfs = [os.path.join(fig_folder, f) for f in os.listdir(fig_folder) if f.endswith('.pdf')]
    for f_img in pdfs:
        img = convert_from_path(f_img, dpi=dpi)[0]
        img.save(os.path.join(
            out_folder,
            os.path.splitext(f_img)[0] + '.jpg'
        ))

    ## TODO handle svg?


if __name__ == '__main__':
    os.makedirs(out_folder, exist_ok=True)

    ## convert figures to jpg
    figures_jpg(dpi=300)

    ## copy bst and cls
    bst_cls = [f for f in os.listdir('.') if f.endswith('.bst') or f.endswith('.cls')]
    for f in bst_cls:
        shutil.copy2(f, out_folder)

    ## process latex_main
    output_lines = expand_latex_rec(latex_main)
    # output_lines = output_lines.replace(r'\revisionadd', '')

    ## write
    with open(os.path.join(out_folder, latex_main), 'w') as outfile:
        outfile.write(output_lines)
