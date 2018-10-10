
main_script=calculation_principles

docs: $(main_script).md
	pandoc --filter pandoc-citeproc $(main_script).md --from=markdown -o $(main_script).docx
pdf: $(main_script).md
	pandoc --filter pandoc-citeproc $(main_script).md --from=markdown -o $(main_script).pdf
html: $(main_script).md
	pandoc --filter pandoc-citeproc $(main_script).md -o $(main_script).html
