# Here are some resources I used to help make this Chip8 interperter.
# http://devernay.free.fr/hacks/chip8/C8TECH10.HTM
# https://en.wikipedia.org/wiki/CHIP-8#Virtual_machine_description
# https://austinmorlan.com/posts/chip8_emulator
# https://code.austinmorlan.com/austin/2019-chip8-emulator/src/branch/master/Source/Chip8.cpp
# https://multigesture.net/articles/how-to-write-an-emulator-chip-8-interpreter/
# https://github.com/AlpacaMax/Python-CHIP8-Emulator/blob/master/chip8.py
# https://github.com/craigthomas/Chip8Python
# https://www.rapidtables.com/convert/number/decimal-to-hex.html
import random
import sys
import threading
import winsound
from tkinter import filedialog as fd
from time import sleep

import pygame

pygame.init()

rom = ""
memory = [0x0] * 4096
registerV = [0x0] * 16
stack = [0x0] * 16
pc = 0x200
ppc = pc
sp = 0
index = 0x0
screenPixels = [0] * (64 * 32)
delay_timer = 0
sound_timer = 0
opcode = 0x0
ttr = 0x0 # Opcode it is actually trying to run
keymap = [
    pygame.K_x,
    pygame.K_1,
    pygame.K_2,
    pygame.K_3,
    pygame.K_q,
    pygame.K_w,
    pygame.K_e,
    pygame.K_a,
    pygame.K_s,
    pygame.K_d,
    pygame.K_z,
    pygame.K_c,
    pygame.K_4,
    pygame.K_r,
    pygame.K_f,
    pygame.K_v,
]
fontset = [
    0xF0,
    0x90,
    0x90,
    0x90,
    0xF0,  # 0
    0x20,
    0x60,
    0x20,
    0x20,
    0x70,  # 1
    0xF0,
    0x10,
    0xF0,
    0x80,
    0xF0,  # 2
    0xF0,
    0x10,
    0xF0,
    0x10,
    0xF0,  # 3
    0x90,
    0x90,
    0xF0,
    0x10,
    0x10,  # 4
    0xF0,
    0x80,
    0xF0,
    0x10,
    0xF0,  # 5
    0xF0,
    0x80,
    0xF0,
    0x90,
    0xF0,  # 6
    0xF0,
    0x10,
    0x20,
    0x40,
    0x40,  # 7
    0xF0,
    0x90,
    0xF0,
    0x90,
    0xF0,  # 8
    0xF0,
    0x90,
    0xF0,
    0x10,
    0xF0,  # 9
    0xF0,
    0x90,
    0xF0,
    0x90,
    0x90,  # A
    0xE0,
    0x90,
    0xE0,
    0x90,
    0xE0,  # B
    0xF0,
    0x80,
    0x80,
    0x80,
    0xF0,  # C
    0xE0,
    0x90,
    0x90,
    0x90,
    0xE0,  # D
    0xF0,
    0x80,
    0xF0,
    0x80,
    0xF0,  # E
    0xF0,
    0x80,
    0xF0,
    0x80,
    0x80,  # F
]


def loadRom(path):
    global rom, memory
    with open(path, mode="rb") as f:
        program = f.read()
    loadOpcodes = []
    for op in program:
        loadOpcodes += [op]
    rom = loadOpcodes
    romSize = len(rom)
    for i in range(romSize):
        memory[0x200 + i] = rom[i]


def emulationCycle():
    global memory, pc, fontset, screenPixels, sp, index, delay_timer
    global sound_timer, keymap, registerV, stack, opcode, ppc, ttr
    pause = False
    for i in range(80):
        memory[0x50 + i] = fontset[i]
    screen = pygame.display.set_mode((64 * 10, 32 * 10))
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if pygame.key.get_pressed()[pygame.K_SPACE]:
                    if pause:
                        pause = False
                    else:
                        pause = True
        ppc = pc
        opcode = (memory[pc] << 8) | memory[pc + 1]
        # print(hex(opcode & 0xFFFF))
        pc += 2
        keysPressed = []
        for i in keymap:
            keysPressed += [1] if pygame.key.get_pressed()[i] else [0]
        if ((opcode & 0xF000) >> 12) == 0x0:
            if opcode & 0x000F == 0xE:
                """
                OPCODE: 0x00EE
                FUNCTION: Return from a sub-routine.
                """
                ttr = "0x00EE"
                sp -= 1
                pc = stack[sp]
            else:
                """
                OPCODE: 0x000E
                FUNCTION: Clears the screen.
                """
                ttr = "0x000E"
                screenPixels = [0] * (64 * 32)
        elif ((opcode & 0xF000) >> 12) == 0x1:
            """
            OPCODE: 0x1nnn
            FUNCTION: Set program counter to nnn.
            """
            ttr = "0x1nnn"
            pc = opcode & 0x0FFF
        elif ((opcode & 0xF000) >> 12) == 0x2:
            """
            OPCODE: 0x2nnn
            FUNCTION: Call a subroutine at nnn.
            """
            ttr = "0x2nnn"
            stack[sp] = pc
            sp += 1
            pc = opcode & 0x0FFF
        elif ((opcode & 0xF000) >> 12) == 0x3:
            """
            OPCODE: 0x3xnn
            FUNCTION: if Vx == nn: Increment program counter by 2.
            """
            ttr = "0x3xnn"
            Vx = registerV[(opcode & 0x0F00) >> 8]
            nn = opcode & 0x00FF
            if Vx == nn:
                pc += 2
        elif ((opcode & 0xF000) >> 12) == 0x4:
            """
            OPCODE: 0x4xnn
            FUNCTION: if Vx != nn: Increment program counter by 2.
            """
            ttr = "0x4xnn"
            Vx = registerV[(opcode & 0x0F00) >> 8]
            nn = opcode & 0x00FF
            if Vx != nn:
                pc += 2
        elif ((opcode & 0xF000) >> 12) == 0x5:
            """
            OPCODE: 0x5xy0
            FUNCTION: if Vx == Vy: Increment program counter by 2.
            """
            ttr = "0x5xy0"
            Vx = registerV[(opcode & 0x0F00) >> 8]
            Vy = registerV[(opcode & 0x00F0) >> 4]
            if Vx == Vy:
                pc += 2
        elif ((opcode & 0xF000) >> 12) == 0x6:
            """
            OPCODE: 0x6xnn
            FUNCTION: Set Vx to nn.
            """
            ttr = "0x6xnn"
            registerV[(opcode & 0x0F00) >> 8] = opcode & 0x00FF
        elif ((opcode & 0xF000) >> 12) == 0x7:
            """
            OPCODE: 0x7xnn
            FUNCTION: Add nn to Vx, then set Vx to the sum.
            """
            ttr = "0x7xnn"
            registerV[(opcode & 0x0F00) >> 8] = (
                registerV[(opcode & 0x0F00) >> 8] + opcode & 0x00FF
            ) & 0xFF
        elif ((opcode & 0xF000) >> 12) == 0x8:
            if opcode & 0x000F == 0x0:
                """
                OPCODE: 0x8xy0
                FUNCTION: Set Vx to Vy.
                """
                ttr = "0x8xy0"
                registerV[(opcode & 0x0F00) >> 8] = registerV[(opcode & 0x00F0) >> 4]
            elif opcode & 0x000F == 0x1:
                """
                OPCODE: 0x8xy1
                FUNCTION: Perform bitwise OR operation on Vx and Vy, then set Vx to the output.
                """
                ttr = "0x8xy1"
                registerV[(opcode & 0x0F00) >> 8] |= registerV[(opcode & 0x00F0) >> 4]
            elif opcode & 0x000F == 0x2:
                """
                OPCODE: 0x8xy2
                FUNCTION: Perform a bitwise AND operation on Vx and Vy, then set Vx to the output.
                """
                ttr = "0x8xy2"
                registerV[(opcode & 0x0F00) >> 8] &= registerV[(opcode & 0x00F0) >> 4]
            elif opcode & 0x000F == 0x3:
                """
                OPCODE: 0x8xy3
                FUNCTION: Perform a bitwise XOR operation on Vx and Vy, then set Vx to the output.
                """
                ttr = "0x8xy3"
                registerV[(opcode & 0x0F00) >> 8] ^= registerV[(opcode & 0x00F0) >> 4]
            elif opcode & 0x000F == 0x4:
                """
                OPCODE: 0x8xy4
                FUNCTION: Add Vy to Vx, but if the result is greater than 255 (8 bits) then set VF to 1. Else 0.
                """
                ttr = "0x8xy4"
                added = (
                    registerV[(opcode & 0x0F00) >> 8]
                    + registerV[(opcode & 0x00F0) >> 4]
                )
                if added > 255:
                    registerV[0xF] = 1
                else:
                    registerV[0xF] = 0
                registerV[(opcode & 0x0F00) >> 8] = added & 0xFF
            elif opcode & 0x000F == 0x5:
                """
                OPCODE: 0x8xy5
                FUNCTION: If Vx > Vy, then set VF to 1. Else 0. Then subtract Vy from Vx then set Vx to that.
                """
                ttr = "0x8xy5"
                registerV[(opcode & 0x0F00) >> 8] = (
                    registerV[(opcode & 0x0F00) >> 8]
                    - registerV[(opcode & 0x00F0) >> 4]
                ) & 0xFF
                if (
                    registerV[(opcode & 0x0F00) >> 8]
                    > registerV[(opcode & 0x00F0) >> 4]
                ):
                    registerV[0xF] = 1
                else:
                    registerV[0xF] = 0
            elif opcode & 0x000F == 0x6:
                """
                OPCODE: 0x8xy6
                FUNCTION: If least significant bit of Vx is 1, then set  VF to 1. Else 0. Then divide Vx by 2.
                """
                ttr = "0x8xy6"
                VF = registerV[(opcode & 0x0F00) >> 8] & 0x1
                registerV[(opcode & 0x0F00) >> 8] >>= 1
                registerV[0xF] = VF
            elif opcode & 0x000F == 0x7:
                """
                OPCODE: 0x8xy7
                FUNCTION: If Vy > Vx, then set VF to 1. Else 0. Then subtract Vx from Vy then set Vx to that.
                """
                ttr = "0x8xy7"
                registerV[(opcode & 0x0F00) >> 8] = (
                    registerV[(opcode & 0x00F0) >> 4]
                    - registerV[(opcode & 0x0F00) >> 8]
                ) & 0xFF
                if (
                    registerV[(opcode & 0x00F0) >> 4]
                    > registerV[(opcode & 0x0F00) >> 8]
                ):
                    registerV[0xF] = 1
                else:
                    registerV[0xF] = 0
            elif opcode & 0x000F == 0xE:
                """
                OPCODE: 0x8xyE
                FUNCTION: If most significant bit of Vx is 1, then set  VF to 1. Else 0. Then multiply Vx by 2.
                """
                ttr = "0x8xyE"
                VF = (registerV[(opcode & 0x0F00) >> 8] & 0x80) >> 7
                registerV[(opcode & 0x0F00) >> 8] = (
                    registerV[(opcode & 0x0F00) >> 8] << 1
                ) & 0x0FF
                registerV[0xF] = VF
        elif ((opcode & 0xF000) >> 12) == 0x9:
            """
            OPCODE: 0x9xy0
            FUNCTION: Increment the program counter by 2 if Vx != Vy.
            """
            ttr = "0x8xy0"
            Vx = registerV[(opcode & 0x0F00) >> 8]
            Vy = registerV[(opcode & 0x00F0) >> 4]
            if Vx != Vy:
                pc += 2
        elif ((opcode & 0xF000) >> 12) == 0xA:
            """
            OPCODE: 0xAnnn
            FUNCTION: Set index to nnn.
            """
            ttr = "0xAnnn"
            index = opcode & 0x0FFF
        elif ((opcode & 0xF000) >> 12) == 0xB:
            """
            OPCODE: 0xBnnn
            FUNCTION: Jump to location nnn + V0
            """
            ttr = "0cBnnn"
            pc = (opcode & 0x0FFF) + registerV[0]
        elif ((opcode & 0xF000) >> 12) == 0xC:
            """
            OPCODE: 0xCxnn
            FUNCTION: The interpreter generates a random number from 0 to 255, which is then ANDed with the value nn. The results are stored in Vx.
            """
            ttr = "0xCxnn"
            randByte = random.randint(0, 255)
            registerV[(opcode & 0x0F00) >> 8] = randByte & (opcode & 0x00FF)
        elif ((opcode & 0xF000) >> 12) == 0xD:
            """
            OPCODE: 0xDxyn
            FUNCTION: Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.
            """
            ttr = "0xDxyn"
            x = registerV[(opcode & 0x0F00) >> 8] % 64
            y = registerV[(opcode & 0x00F0) >> 4] % 32
            registerV[0xF] = 0
            for row in range(opcode & 0x000F):
                sByte = memory[index + row]
                for col in range(8):
                    if (sByte & (0x80 >> col)) != 0:
                        if screenPixels[(x + col + ((y + row) * 64)) % (64 * 32)] == 1:
                            registerV[0xF] = 1
                        screenPixels[(x + col + ((y + row) * 64)) % (64 * 32)] ^= 1
        elif ((opcode & 0xF000) >> 12) == 0xE:
            if opcode & 0x000F == 0xE:
                """
                OPCODE: 0xEx9E
                FUNCTION: Increment the program counter by 2 if the key with the value of Vx is pressed.
                """
                ttr = "0xEx9E"
                if keysPressed[registerV[(opcode & 0x0F00) >> 8]] != 0:
                    pc += 2
            else:
                """
                OPCODE: 0xExA1
                FUNCTION: Incrememt the program counter by 2 if the key with the value of Vx is not currently pressed.
                """
                ttr = "0xExA1"
                if keysPressed[registerV[(opcode & 0x0F00) >> 8]] == 0:
                    pc += 2
        elif ((opcode & 0xF000) >> 12) == 0xF:
            if opcode & 0x000F == 0x7:
                """
                OPCODE: Fx07
                FUNCTION: Set Vx to the value of the delay timer.
                """
                ttr = "0xFx07"
                registerV[(opcode & 0x0F00) >> 8] = delay_timer
            elif opcode & 0x000F == 0xA:
                """
                OPCODE: Fx0A
                FUNCTION: Wait until a key is pressed then store the value in Vx
                """
                ttr = "0xFx0A"
                if 1 in keysPressed:
                    registerV[(opcode & 0x0F00) >> 8] = keysPressed.index(1)
                else:
                    pc -= 2
            elif opcode & 0x000F == 0x5:
                if ((opcode & 0x00F0) >> 4) == 0x1:
                    """
                    OPCODE: 0xFx15
                    FUNCTION: Set the delay timer to Vx
                    """
                    ttr = "0xFx15"
                    delay_timer = registerV[(opcode & 0x0F00) >> 8]
                elif ((opcode & 0x00F0) >> 4) == 0x5:
                    """
                    OPCODE: 0xFx55
                    FUNCTION: Store registers V0 through Vx in memory starting at location index.
                    """
                    ttr = "0xFx55"
                    for i in range(0, ((opcode & 0x0F00) >> 8) + 1, 1):
                        memory[index + i] = registerV[i]
                else:
                    """
                    OPCODE: 0xFx65
                    FUNCTION: Read registers V0 through Vx from memory starting at location index.
                    """
                    ttr = "0xFx65"
                    for i in range(0, ((opcode & 0x0F00) >> 8) + 1, 1):
                        registerV[i] = memory[index + i]
            elif opcode & 0x000F == 0x8:
                """
                OPCODE: 0xFx18
                FUNCTION: Set the sound timer to Vx
                """
                ttr = "0xFx18"
                sound_timer = registerV[(opcode & 0x0F00) >> 8]
            elif opcode & 0x000F == 0xE:
                """
                OPCODE: 0xFx1E
                FUNTION: Add I and Vx and store the result in I
                """
                ttr = "0xFx1E"
                index += registerV[(opcode & 0x0F00) >> 8]
            elif opcode & 0x000F == 0x9:
                """
                OPCODE: 0xFx29
                FUNCTION: Set index to the location of sprite for digit Vx.
                """
                ttr = "0xFx29"
                index = 0x50 + (5 * registerV[(opcode & 0x0F00) >> 8])
            elif opcode & 0x000F == 0x3:
                """
                OPCODE: 0xFx33
                FUNCTION: Store BCD representation of Vx in memory locations index, index + 1, and index + 2.
                """
                ttr = "0xFx33"
                value = registerV[(opcode & 0x0F00) >> 8]
                memory[index + 2] = value % 10
                value /= 10
                memory[index + 1] = int(value % 10)
                value /= 10
                memory[index] = int(value % 10)
        screen.fill((0, 0, 0))
        currentPixel = -1
        for y in range(32):  # Draw display
            for x in range(64):
                currentPixel += 1
                if screenPixels[currentPixel] != 0:
                    pygame.draw.rect(
                        screen,
                        (255, 255, 255),
                        pygame.Rect((x * 10, y * 10), (10, 10)),
                    )
        pygame.display.flip()
        if delay_timer > 0:
            delay_timer -= 1
        if sound_timer > 0:
            sound_timer -= 1
        if pause:
            while True:
                wb = False
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if pygame.key.get_pressed()[pygame.K_n] or pygame.key.get_pressed()[pygame.K_SPACE]:
                            wb = True
                            if pygame.key.get_pressed()[pygame.K_SPACE]:
                                pause = False
                if wb:
                    break



class Beeping(threading.Thread):
    def __init__(self, beeps):
        threading.Thread.__init__(self)
        self.runnable = beeps
        self.daemon = True

    def run(self):
        self.runnable()


def beeps():
    global sound_timer
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        if sound_timer == 1:
            winsound.Beep(500, 100)


beepfunc = Beeping(beeps)
beepfunc.start()


class DebugTerminal(threading.Thread):
    def __init__(self, debugTerm):
        threading.Thread.__init__(self)
        self.runnable = debugTerm
        self.daemon = True

    def run(self):
        self.runnable()


def debugTerm():
    global registerV, opcode, ppc, delay_timer, sound_timer, ttr
    print("\033[8;40;80t")
    print("Starting debugging process.")
    print("\n" * 22)
    while True:
        print("\033[22A")
        for i in range(16):
            print("V" + hex(i)[-1].upper() + ": " + hex(registerV[i])[2:] + "            ")
        print("opcode: " + hex(opcode & 0xFFFF))
        print("opcode actually running: " + str(ttr))
        print("pc: " + hex(ppc))
        print("DT: " + str(delay_timer))
        print("ST: " + str(sound_timer))
debugF = DebugTerminal(debugTerm)


loadRom(
    fd.askopenfilename(
        title="Select A Chip8 Rom",
        filetypes=(("Chip8 Roms", "*.ch8"), ("All Files", "*.*")),
    )
)
if True:
    debugF.start()
emulationCycle()
