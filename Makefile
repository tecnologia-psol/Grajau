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
	echo "Começando em" > time.log
	date >> time.log 
	time make run >> time.log ;
	echo "Finalizado em" >> time.log 
	date >> time.log 

centroids:
	make clear
	python main.py --compile-centroids