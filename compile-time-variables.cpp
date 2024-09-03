// https://godbolt.org/z/W8GT7oqqq

template<int i, int j> struct bit_holder;

template<int i, int j>
consteval bool process_bit() {
    return requires { sizeof(bit_holder<i*0, j*0>); };
}

template<int idx, int val>
consteval void set_var()
{
    process_bit<idx, val&1>();
    process_bit<idx, val&2>();
    process_bit<idx, val&4>();
    process_bit<idx, val&8>();
    process_bit<idx, val&16>();
    process_bit<idx, val&32>();
    process_bit<idx, val&64>();
    process_bit<idx, val&128>();
}

template<int idx>
consteval int get_var()
{
    return !process_bit<idx, 1>()*1 +
           !process_bit<idx, 2>()*2 +
           !process_bit<idx, 4>()*4 +
           !process_bit<idx, 8>()*8 +
           !process_bit<idx, 16>()*16 +
           !process_bit<idx, 32>()*32 +
           !process_bit<idx, 64>()*64 +
           !process_bit<idx, 128>()*128;
}


consteval void set_vars()
{
    set_var<0, 'h'>();
    set_var<1, 'e'>();
    set_var<2, 'l'>();
    set_var<3, 'l'>();
    set_var<4, 'o'>();
}

template<> struct bit_holder<0, (set_vars(),0)> {};

#include <stdio.h>
int main()
{
    char buf[6] = {
        get_var<0>(), get_var<1>(), get_var<2>(),
        get_var<3>(), get_var<4>(), '\0'
    };
    puts(buf);
}
