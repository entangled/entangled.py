# ~/~ begin <<doc/index.md#Makefile>>[init]
.RECIPEPREFIX = >
.PHONY: clean

build_dir = ./build
source_files = src/euler_number.cc

obj_files = $(source_files:%.cc=$(build_dir)/%.o)
dep_files = $(obj_files:%.o=%.d)

euler: $(obj_files)
> @echo -e "Linking \e[32;1m$@\e[m"
> @gcc $^ -o $@

$(build_dir)/%.o: %.c
> @echo -e "Compiling \e[33m$@\e[m"
> @mkdir -p $(@D)
> @gcc -MMD -c $< -o $@

clean:
> rm -rf build euler

-include $(dep_files)
# ~/~ end
