# Makefile

all:
	echo hello

clean:
	A="$(shell find . -name '__pycache__')"; for i in $$A; do rm -rf $$i; done
	A="$(shell find . -name '*.pyc')"; for i in $$A; do rm -rf $$i; done
	A="$(shell find . -name '*~')"; for i in $$A; do rm -rf $$i; done

# eof
