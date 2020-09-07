import os
import io
import shutil
import re
import sys

USAGE = \
"""arxivify.py main.tex output_dir

main.tex should be your main tex file, which potentially includes others
output_dir is the output directory to write the flattened output tex and images to
"""

if len(sys.argv) != 3:
    print(USAGE)
    sys.exit(1)

match_bibliography = re.compile("^\s*\\\\bibliography\{(.*)\}")
match_use_package = re.compile("^\s*\\\\usepackage.*\{(.*)\}")
match_tex_input = re.compile("^\s*\\\\input\{(.*)\}")
match_include_graphics = re.compile("^\s*\\\\includegraphics.*\{(.*)\}")

found_bibliography = False
uses_minted = False
bib_files = []

def get_tex_content(tex_file, base_path, output_dir):
    content = ""
    with io.open(tex_file, "r", encoding="utf-8") as f:
        for l in f:
            m = match_tex_input.match(l)
            if m:
                file_path = os.path.join(base_path, os.path.normpath(m.group(1)))
                content += "%include of {}\n".format(file_path)
                content += get_tex_content(file_path, base_path, output_dir) + "\n"
                continue
            m = match_use_package.match(l)
            if m:
                package = m.group(1)
                if package == "minted":
                    global uses_minted
                    uses_minted = True
            m = match_bibliography.match(l)
            if m:
                bib_files.append(m.group(1) + ".bib")
                if found_bibliography:
                    continue
                bib_name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
                l = "\\bibliography{" + bib_name + "}\n"
            m = match_include_graphics.match(l)
            if m:
                img_path = os.path.join(base_path, os.path.normpath(m.group(1)))
                output_path = os.path.join(output_dir, os.path.basename(img_path))
                open_brace = l.find("{")
                l = l[0:open_brace + 1] + os.path.basename(img_path) + "}"
                shutil.copy2(img_path, output_path)
            content += l
    return content

filename = os.path.abspath(sys.argv[1])
base_dir = os.path.dirname(filename)
output_dir = os.path.abspath(sys.argv[2])
tex_content = get_tex_content(filename, base_dir, output_dir)

# Collect all the bib files into one
bib_content = ""
for b in bib_files:
    print(b)
    with io.open(os.path.join(base_dir, b), "r", encoding="utf-8") as f:
        bib_content += f.read()

try:
    os.mkdir(output_dir)
except:
    pass

output_file = os.path.join(output_dir, os.path.basename(filename))
with io.open(output_file, "w", encoding="utf-8") as f:
    f.write(tex_content)

output_bib = os.path.splitext(output_file)[0] + ".bib"
print(output_bib)
with io.open(output_bib, "w", encoding="utf-8") as f:
    f.write(bib_content)

print("Almost done! Now copy any custom cls or bst style files used to {output} and generate your bbl file".format(output=output_dir))

if uses_minted:
    print("For minted:")
    print("  Make sure to build your minted cache with \\usepackage[finalizecache=true,cachedir=./]{minted}")
    print("  and then use the frozen cache before uploading to arXiv with \\usepackage[frozencache=true,cachedir=./]{minted}")

