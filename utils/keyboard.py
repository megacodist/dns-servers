import enum


class Modifiers(enum.IntFlag):
    """Specifies modifiers for Key event. The 'state' attribute of Key event
    is an integer (actually a bit mask) which every bit specifies a modifier
    such as Alt, Num Lock, Button-1 (left mouse button) ans so on.
    """
    NONE = 0x0000
    SHIFT = 0x0001
    CAPS_LOCK = 0x0002
    CONTROL = 0x0004
    NUM_LOCK = 0x0008
    SCROLL_LOCK = 0x0020
    BUTTON_1 = 0x0100
    BUTTON_2 = 0x0200
    BUTTON_3 = 0x0400
    ALT = 0x20000


class KeyCodes(enum.IntEnum):
    BRACELEFT = 219
    BRACERIGHT = 221
    BRACKETLEFT = 219
    BRACKETRIGHT = 221
    LESS = 188
    GREATER = 190
    BACKSLASH = 220
    SLASH = 111
    SEMICOLON = 186
    APOSTROPHE = 222
    COMMA = 188
    PERIOD_KB = 190
    PERIOD_KP = 110
    BAR = 220
    COLON = 186
    QUOTEDBL = 222
    BACKSPACE = 8
    ASCIITILDE = 192
    EXCLAM = 49
    AT = 50
    NUMBERSIGN = 51
    DOLLAR = 52
    PERCENT = 53
    ASCIICIRCUM = 54
    AMPERSAND = 55
    ASTERISK_KB = 56
    ASTERISK_KP = 106
    PARENLEFT = 57
    PARENRIGHT = 48
    UNDERSCORE = 189
    PLUS_KB = 187
    PLUS_KP = 107
    SPACE = 32

    DELETE = 46
    END = 35
    NEXT = 34
    INSERT = 45
    HOME = 36
    PRIOR = 33
    PAUSE = 19

    NUM_LOCK = 144
    SCROLL_LOCK = 145
    CAPS_LOCK = 20
    
    MINUS = 109
    RETURN = 13
    TAB = 9
    
    LEFT = 37
    UP = 38
    RIGHT = 39
    DOWN = 40

    SHIFT_L = 16
    SHIFT_R = 16
    CONTROL_L = 17
    CONTROL_R = 17
    ALT_L = 18
    ALT_R = 18
    WIN_L = 91
    WIN_R = 92

    KB_0 = 48
    KB_1 = 49
    KB_2 = 50
    KB_3 = 51
    KB_4 = 52
    KB_5 = 53
    KB_6 = 54
    KB_7 = 55
    KB_8 = 56
    KB_9 = 57

    KP_0 = 96
    KP_1 = 97
    KP_2 = 98
    KP_3 = 99
    KP_4 = 100
    KP_5 = 101
    KP_6 = 102
    KP_7 = 103
    KP_8 = 104
    KP_9 = 105
    
    A = 65
    B = 66
    C = 67
    D = 68
    E = 69
    F = 70
    G = 71
    H = 72
    I = 73
    J = 74
    K = 75
    L = 76
    M = 77
    N = 78
    O = 79
    P = 80
    Q = 81
    R = 82
    S = 83
    T = 84
    U = 85
    V = 86
    W = 87
    X = 88
    Y = 89
    Z = 90

    F1 = 112
    F2 = 113
    F3 = 114
    F4 = 115
    F5 = 116
    F6 = 117
    F7 = 118
    F8 = 119
    F9 = 120
    F10 = 121
    F11 = 122
    F12 = 123
