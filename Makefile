get_deps:
	echo "TODO"

run:
	make clear
	python main.py

report:
	make clear
	mkdir tmp
	cd tmp; \
		latexmk ../relatorio/Relatorio.tex -pdf --shell-escape -xelatex

clear:
	yes | rm -R ./tmp || true
	yes | rm -R ./to/* || true

time:
	{ time make run > time.log ; } 2> time.log