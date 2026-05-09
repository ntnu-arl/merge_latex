from pathlib import Path
import shutil
from PIL import Image
from pdf2image import convert_from_path


out_folder = 'submission_material'
fig_folder = 'figs'
latex_main = 'main.tex'
glossary = {}
shortcuts = {}
figure_paths = []


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


# def glossary_dict(path: str):
#     global glossary, shortcuts

#     with Path(path).open('r') as infile:
#         lines = infile.readlines()

#     for l in lines:
#         if '\\DeclareAcronym' in l:
#             key = l.split('{')[1].split('}')[0]
#             glossary[key] = GlossaryEntry(key)
#         elif 'short = ' in l:
#             glossary[key].short = l.split(' = ')[1].split(',')[0]
#         elif 'long = ' in l:
#             glossary[key].long = l.split(' = ')[1].split(',')[0].split('\n')[0]
#         elif 'first-style = short' in l:
#             glossary[key].first = 'short'
#         elif 'first-style = long' in l:
#             glossary[key].first = 'long'
#         elif 'long-plural-form' in l:
#             glossary[key].long_plural = l.split(' = ')[1].split(',')[0].split('\n')[0]
#         elif 'short-plural-form' in l:
#             glossary[key].short_plural = l.split(' = ')[1].split(',')[0].split('\n')[0]
#         elif '\\newcommand{' in l:
#             key = l.split('{')[1].split('}')[0]
#             val = (l.split('{')[2] + '{' + l.split('{')[3]).split('}')[0] + '}'
#             shortcuts[key] = val

#     for key in glossary.keys():
#         glossary[key].short = expand_line(glossary[key].short)
#         glossary[key].long = expand_line(glossary[key].long)

#     for key in glossary.keys():
#         glossary[key].used = False


def expand_line(l: str):
    global glossary, shortcuts

    if len(l) == 1:
        return l
    if not l.split() or l.split()[0].startswith('%'):
        return ''

    # print(l)

    # if '\\acresetall' in l:
    #     for key in glossary.keys():
    #         glossary[key].used = False
    #     return ''

    # for key in shortcuts.keys():
    #     if key in l.replace('-', ' ').replace(',', ' ').replace('.', ' ').replace('~', ' ').replace('\'', ' ').replace('(', ' ').replace(')', ' ').split():
    #         l = l.replace(key, shortcuts[key])

    # nb_ac = l.count('\\ac')
    # for i in range(nb_ac):
    #     start = l.find('\\ac')
    #     command = l[start:].split('{')[0]
    #     key = l[start+len(command)+1:].split('}')[0]
    #     if command == '\\ac':
    #         expanded = glossary[key].s()
    #     elif command == '\\acf':
    #         expanded = glossary[key].s_first()
    #     elif command == '\\acs':
    #         expanded = glossary[key].s_short()
    #     elif command == '\\acl':
    #         expanded = glossary[key].s_long()
    #     elif command == '\\acp':
    #         expanded = glossary[key].s(plural=True)
    #     elif command in ['\\acfp', '\\acpf']:
    #         expanded = glossary[key].s_first(plural=True)
    #     elif command in ['\\acsp', '\\acps']:
    #         expanded = glossary[key].s_short(plural=True)
    #     elif command in ['\\aclp', '\\acpl']:
    #         expanded = glossary[key].s_long(plural=True)
        # l = l.replace(command +'{' + key + '}', expanded)
    return l


def expand_latex_rec(path: str):
    global glossary, figure_paths
    output_lines = ''

    with Path(path).open('r') as infile:
        lines = infile.readlines()

    for l in lines:
        if len(l) == 1:
            output_lines += l
        elif not l.split() or l.split()[0].startswith('%'):
            continue
        elif r'\input{' in l:
            input_path = Path(l.split('{')[1].split('}')[0])
            if input_path.suffix != '.tex':
                input_path = input_path.with_suffix('.tex')
            output_lines += expand_latex_rec(input_path) + '\n'
        elif r'\includegraphics' in l:
            figure_path = Path(l.split('{')[1].split('}')[0])
            figure_paths.append(figure_path)
            output_lines += l.replace(figure_path.as_posix(), figure_path.stem + '.jpg')
        elif r'\bibliography{' in l:
            output_lines += expand_latex_rec('main.bbl') + '\n'
        else:
            output_lines += l
    return output_lines


def figures_jpg(dpi=200):
    global figure_paths 

    ## convert image figures to jpg
    seen = set()
    for f_img in figure_paths:
        print(f_img)
        f_img = Path(f_img)

        if f_img in seen:
            continue
        seen.add(f_img)

        out_path = out_folder / f'{f_img.stem}.jpg'

        if f_img.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            img = Image.open(f_img).convert("RGB")
            img.save(out_path)
        elif f_img.suffix.lower() == '.pdf':
            img = convert_from_path(f_img, dpi=dpi)[0]
            img.save(out_path)
        else:
            print(f'WARNING: unsupported figure format: {f_img}')

if __name__ == '__main__':
    out_folder = Path(out_folder)
    fig_folder = Path(fig_folder)

    out_folder.mkdir(exist_ok=True)

    ## copy bst and cls
    bst_cls = [f for f in Path('.').iterdir() if f.suffix in ('.bst', '.cls')]
    for f in bst_cls:
        shutil.copy2(f, out_folder)

    ## process latex_main
    output_lines = expand_latex_rec(latex_main)

    ## convert figures to jpg
    # figures_jpg(dpi=300)

    ## write
    with (out_folder / latex_main).open('w') as outfile:
        outfile.write(output_lines)
