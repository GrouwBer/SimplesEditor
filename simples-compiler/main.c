/*
 * Simples Compiler — mock didatico que gera NASM 32-bit valido.
 *
 * Versao mock: gera um programa NASM i386 que imprime uma saudacao
 * e encerra. Suficiente para validar todo o pipeline:
 * simplesc → NASM → nasm → .o → ld → ELF → qemu-i386 → output
 *
 * Formato de uso: simplesc <arquivo.simples>
 * O argumento e ignorado — sempre gera o mesmo NASM de demonstracao.
 */
#include <stdio.h>

int main(void) {
    printf(
        "section .text\n"
        "    global _start\n"
        "\n"
        "_start:\n"
        "    ; sys_write(1, msg, msg_len)\n"
        "    mov eax, 4          ; syscall: write\n"
        "    mov ebx, 1          ; fd: stdout\n"
        "    mov ecx, msg        ; buffer\n"
        "    mov edx, msg_len    ; tamanho\n"
        "    int 0x80            ; chama kernel\n"
        "\n"
        "    ; sys_exit(0)\n"
        "    mov eax, 1          ; syscall: exit\n"
        "    xor ebx, ebx        ; status: 0\n"
        "    int 0x80            ; chama kernel\n"
        "\n"
        "section .data\n"
        "msg:    db 'Ola Simples!', 0xa\n"
        "msg_len equ $ - msg\n"
    );
    return 0;
}
