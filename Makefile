get_deps:
	echo "TODO"
run:
	python main.py
report:
	make clear
	mkdir tmp
	cd tmp; \
		latexmk ../relatorio/Relatorio.tex -pdf --shell-escape -xelatex
		
clear:
	yes | rm -R ./tmp || true
	yes | rm -R ./to/* || true