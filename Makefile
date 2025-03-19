ALL_TESTS ?= $(wildcard tests/*.uc)
PHASE1_TESTS ?= tests/type_clash_user.uc tests/function_clash_primitive.uc
PHASE2_TESTS ?= tests/phase2.uc tests/unknown_type.uc
PHASE3_TESTS ?= tests/unknown_function.uc
PHASE4_TESTS ?= tests/variable_clash.uc tests/self_init.uc
PHASE5_TESTS ?= tests/break_not_in_loop.uc
PHASE6_TESTS ?= $(filter-out $(PHASE1_TESTS) $(PHASE2_TESTS) $(PHASE3_TESTS) $(PHASE4_TESTS) $(PHASE5_TESTS),$(ALL_TESTS))
CUSTOM_TESTS ?= $(wildcard *.uc)
PYTHON ?= python3
FLAGS ?= -S -T

all: test

test: phase1 phase2 phase3 phase4 phase5 phase6 custom

phase1: $(PHASE1_TESTS:.uc=.test)

phase2: $(PHASE2_TESTS:.uc=.test)

phase3: $(PHASE3_TESTS:.uc=.test)

phase4: $(PHASE4_TESTS:.uc=.test)

phase5: $(PHASE5_TESTS:.uc=.test)

phase6: $(PHASE6_TESTS:.uc=.test)

custom: $(CUSTOM_TESTS:.uc=.test)

%.test: %.uc
	@echo "Testing $<..."
	@rm -f $*.out $*.err $*.types
	$(PYTHON) ucc.py $(FLAGS) $< > $*.out 2> $*.err || true
	@!(grep -qs '^Traceback' $*.err) || !(echo "### Error: ucc crashed ###" && cat $*.err)
	$(PYTHON) ucccheck.py $<
	@echo

%.graph: %.uc
	@echo "Generating graph for $<..."
	$(PYTHON) ucparser.py $<
	dot -Tpdf -o $*.pdf $*.dot
	rm -f $*.dot
	@echo

STYLE_SOURCES ?= ucbase.py ucexpr.py ucfunctions.py ucstmt.py uctypes.py
PYLINT_FLAGS ?= --disable R0913,R0917 --max-module-lines=1500

style: style-pycode style-pydoc style-pylint

style-pycode:
	pycodestyle $(STYLE_SOURCES)

style-pydoc:
	pydocstyle $(STYLE_SOURCES)

style-pylint:
	pylint $(PYLINT_FLAGS) $(STYLE_SOURCES)

clean:
	rm -f tests/*.out tests/*.err tests/*.types tests/*.dot
