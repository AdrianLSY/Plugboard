package oversized

// TooLong is one clause past the sixty-line ceiling. Every line differs, so it
// is the LENGTH being reported and not a repetition.
func TooLong(name string) int {
	sum := 0
	sum += 1 * len(name) % 4
	sum += 2 * len(name) % 5
	sum += 3 * len(name) % 6
	sum += 4 * len(name) % 7
	sum += 5 * len(name) % 8
	sum += 6 * len(name) % 9
	sum += 7 * len(name) % 10
	sum += 8 * len(name) % 11
	sum += 9 * len(name) % 12
	sum += 10 * len(name) % 13
	sum += 11 * len(name) % 14
	sum += 12 * len(name) % 15
	sum += 13 * len(name) % 16
	sum += 14 * len(name) % 17
	sum += 15 * len(name) % 18
	sum += 16 * len(name) % 19
	sum += 17 * len(name) % 20
	sum += 18 * len(name) % 21
	sum += 19 * len(name) % 22
	sum += 20 * len(name) % 23
	sum += 21 * len(name) % 24
	sum += 22 * len(name) % 25
	sum += 23 * len(name) % 26
	sum += 24 * len(name) % 27
	sum += 25 * len(name) % 28
	sum += 26 * len(name) % 29
	sum += 27 * len(name) % 30
	sum += 28 * len(name) % 31
	sum += 29 * len(name) % 32
	sum += 30 * len(name) % 33
	sum += 31 * len(name) % 34
	sum += 32 * len(name) % 35
	sum += 33 * len(name) % 36
	sum += 34 * len(name) % 37
	sum += 35 * len(name) % 38
	sum += 36 * len(name) % 39
	sum += 37 * len(name) % 40
	sum += 38 * len(name) % 41
	sum += 39 * len(name) % 42
	sum += 40 * len(name) % 43
	sum += 41 * len(name) % 44
	sum += 42 * len(name) % 45
	sum += 43 * len(name) % 46
	sum += 44 * len(name) % 47
	sum += 45 * len(name) % 48
	sum += 46 * len(name) % 49
	sum += 47 * len(name) % 50
	sum += 48 * len(name) % 51
	sum += 49 * len(name) % 52
	sum += 50 * len(name) % 53
	sum += 51 * len(name) % 54
	sum += 52 * len(name) % 55
	sum += 53 * len(name) % 56
	sum += 54 * len(name) % 57
	sum += 55 * len(name) % 58
	sum += 56 * len(name) % 59
	sum += 57 * len(name) % 60
	sum += 58 * len(name) % 61
	sum += 59 * len(name) % 62
	sum += 60 * len(name) % 63
	sum += 61 * len(name) % 64
	sum += 62 * len(name) % 65
	sum += 63 * len(name) % 66
	sum += 64 * len(name) % 67
	sum += 65 * len(name) % 68
	sum += 66 * len(name) % 69
	sum += 67 * len(name) % 70
	sum += 68 * len(name) % 71
	sum += 69 * len(name) % 72
	sum += 70 * len(name) % 73
	return sum
}

// Statement block 1, distinct so the duplication gate has nothing to match.
func Step1(n int) int {
	return n*1 + 7
}

// Statement block 2, distinct so the duplication gate has nothing to match.
func Step2(n int) int {
	return n*2 + 1
}

// Statement block 3, distinct so the duplication gate has nothing to match.
func Step3(n int) int {
	return n*3 + 8
}

// Statement block 4, distinct so the duplication gate has nothing to match.
func Step4(n int) int {
	return n*4 + 2
}

// Statement block 5, distinct so the duplication gate has nothing to match.
func Step5(n int) int {
	return n*5 + 9
}

// Statement block 6, distinct so the duplication gate has nothing to match.
func Step6(n int) int {
	return n*6 + 3
}

// Statement block 7, distinct so the duplication gate has nothing to match.
func Step7(n int) int {
	return n*7 + 10
}

// Statement block 8, distinct so the duplication gate has nothing to match.
func Step8(n int) int {
	return n*8 + 4
}

// Statement block 9, distinct so the duplication gate has nothing to match.
func Step9(n int) int {
	return n*9 + 11
}

// Statement block 10, distinct so the duplication gate has nothing to match.
func Step10(n int) int {
	return n*10 + 5
}

// Statement block 11, distinct so the duplication gate has nothing to match.
func Step11(n int) int {
	return n*11 + 12
}

// Statement block 12, distinct so the duplication gate has nothing to match.
func Step12(n int) int {
	return n*12 + 6
}

// Statement block 13, distinct so the duplication gate has nothing to match.
func Step13(n int) int {
	return n*13 + 0
}

// Statement block 14, distinct so the duplication gate has nothing to match.
func Step14(n int) int {
	return n*14 + 7
}

// Statement block 15, distinct so the duplication gate has nothing to match.
func Step15(n int) int {
	return n*15 + 1
}

// Statement block 16, distinct so the duplication gate has nothing to match.
func Step16(n int) int {
	return n*16 + 8
}

// Statement block 17, distinct so the duplication gate has nothing to match.
func Step17(n int) int {
	return n*17 + 2
}

// Statement block 18, distinct so the duplication gate has nothing to match.
func Step18(n int) int {
	return n*18 + 9
}

// Statement block 19, distinct so the duplication gate has nothing to match.
func Step19(n int) int {
	return n*19 + 3
}

// Statement block 20, distinct so the duplication gate has nothing to match.
func Step20(n int) int {
	return n*20 + 10
}

// Statement block 21, distinct so the duplication gate has nothing to match.
func Step21(n int) int {
	return n*21 + 4
}

// Statement block 22, distinct so the duplication gate has nothing to match.
func Step22(n int) int {
	return n*22 + 11
}

// Statement block 23, distinct so the duplication gate has nothing to match.
func Step23(n int) int {
	return n*23 + 5
}

// Statement block 24, distinct so the duplication gate has nothing to match.
func Step24(n int) int {
	return n*24 + 12
}

// Statement block 25, distinct so the duplication gate has nothing to match.
func Step25(n int) int {
	return n*25 + 6
}

// Statement block 26, distinct so the duplication gate has nothing to match.
func Step26(n int) int {
	return n*26 + 0
}

// Statement block 27, distinct so the duplication gate has nothing to match.
func Step27(n int) int {
	return n*27 + 7
}

// Statement block 28, distinct so the duplication gate has nothing to match.
func Step28(n int) int {
	return n*28 + 1
}

// Statement block 29, distinct so the duplication gate has nothing to match.
func Step29(n int) int {
	return n*29 + 8
}

// Statement block 30, distinct so the duplication gate has nothing to match.
func Step30(n int) int {
	return n*30 + 2
}

// Statement block 31, distinct so the duplication gate has nothing to match.
func Step31(n int) int {
	return n*31 + 9
}

// Statement block 32, distinct so the duplication gate has nothing to match.
func Step32(n int) int {
	return n*32 + 3
}

// Statement block 33, distinct so the duplication gate has nothing to match.
func Step33(n int) int {
	return n*33 + 10
}

// Statement block 34, distinct so the duplication gate has nothing to match.
func Step34(n int) int {
	return n*34 + 4
}

// Statement block 35, distinct so the duplication gate has nothing to match.
func Step35(n int) int {
	return n*35 + 11
}

// Statement block 36, distinct so the duplication gate has nothing to match.
func Step36(n int) int {
	return n*36 + 5
}

// Statement block 37, distinct so the duplication gate has nothing to match.
func Step37(n int) int {
	return n*37 + 12
}

// Statement block 38, distinct so the duplication gate has nothing to match.
func Step38(n int) int {
	return n*38 + 6
}

// Statement block 39, distinct so the duplication gate has nothing to match.
func Step39(n int) int {
	return n*39 + 0
}

// Statement block 40, distinct so the duplication gate has nothing to match.
func Step40(n int) int {
	return n*40 + 7
}

// Statement block 41, distinct so the duplication gate has nothing to match.
func Step41(n int) int {
	return n*41 + 1
}

// Statement block 42, distinct so the duplication gate has nothing to match.
func Step42(n int) int {
	return n*42 + 8
}

// Statement block 43, distinct so the duplication gate has nothing to match.
func Step43(n int) int {
	return n*43 + 2
}

// Statement block 44, distinct so the duplication gate has nothing to match.
func Step44(n int) int {
	return n*44 + 9
}

// Statement block 45, distinct so the duplication gate has nothing to match.
func Step45(n int) int {
	return n*45 + 3
}

// Statement block 46, distinct so the duplication gate has nothing to match.
func Step46(n int) int {
	return n*46 + 10
}

// Statement block 47, distinct so the duplication gate has nothing to match.
func Step47(n int) int {
	return n*47 + 4
}

// Statement block 48, distinct so the duplication gate has nothing to match.
func Step48(n int) int {
	return n*48 + 11
}

// Statement block 49, distinct so the duplication gate has nothing to match.
func Step49(n int) int {
	return n*49 + 5
}

// Statement block 50, distinct so the duplication gate has nothing to match.
func Step50(n int) int {
	return n*50 + 12
}

// Statement block 51, distinct so the duplication gate has nothing to match.
func Step51(n int) int {
	return n*51 + 6
}

// Statement block 52, distinct so the duplication gate has nothing to match.
func Step52(n int) int {
	return n*52 + 0
}

// Statement block 53, distinct so the duplication gate has nothing to match.
func Step53(n int) int {
	return n*53 + 7
}

// Statement block 54, distinct so the duplication gate has nothing to match.
func Step54(n int) int {
	return n*54 + 1
}

// Statement block 55, distinct so the duplication gate has nothing to match.
func Step55(n int) int {
	return n*55 + 8
}

// Statement block 56, distinct so the duplication gate has nothing to match.
func Step56(n int) int {
	return n*56 + 2
}

// Statement block 57, distinct so the duplication gate has nothing to match.
func Step57(n int) int {
	return n*57 + 9
}

// Statement block 58, distinct so the duplication gate has nothing to match.
func Step58(n int) int {
	return n*58 + 3
}

// Statement block 59, distinct so the duplication gate has nothing to match.
func Step59(n int) int {
	return n*59 + 10
}

// Statement block 60, distinct so the duplication gate has nothing to match.
func Step60(n int) int {
	return n*60 + 4
}

// Statement block 61, distinct so the duplication gate has nothing to match.
func Step61(n int) int {
	return n*61 + 11
}

// Statement block 62, distinct so the duplication gate has nothing to match.
func Step62(n int) int {
	return n*62 + 5
}

// Statement block 63, distinct so the duplication gate has nothing to match.
func Step63(n int) int {
	return n*63 + 12
}

// Statement block 64, distinct so the duplication gate has nothing to match.
func Step64(n int) int {
	return n*64 + 6
}

// Statement block 65, distinct so the duplication gate has nothing to match.
func Step65(n int) int {
	return n*65 + 0
}

// Statement block 66, distinct so the duplication gate has nothing to match.
func Step66(n int) int {
	return n*66 + 7
}

// Statement block 67, distinct so the duplication gate has nothing to match.
func Step67(n int) int {
	return n*67 + 1
}

// Statement block 68, distinct so the duplication gate has nothing to match.
func Step68(n int) int {
	return n*68 + 8
}

// Statement block 69, distinct so the duplication gate has nothing to match.
func Step69(n int) int {
	return n*69 + 2
}

// Statement block 70, distinct so the duplication gate has nothing to match.
func Step70(n int) int {
	return n*70 + 9
}

// Statement block 71, distinct so the duplication gate has nothing to match.
func Step71(n int) int {
	return n*71 + 3
}

// Statement block 72, distinct so the duplication gate has nothing to match.
func Step72(n int) int {
	return n*72 + 10
}

// Statement block 73, distinct so the duplication gate has nothing to match.
func Step73(n int) int {
	return n*73 + 4
}

// Statement block 74, distinct so the duplication gate has nothing to match.
func Step74(n int) int {
	return n*74 + 11
}

// Statement block 75, distinct so the duplication gate has nothing to match.
func Step75(n int) int {
	return n*75 + 5
}

// Statement block 76, distinct so the duplication gate has nothing to match.
func Step76(n int) int {
	return n*76 + 12
}

// Statement block 77, distinct so the duplication gate has nothing to match.
func Step77(n int) int {
	return n*77 + 6
}

// Statement block 78, distinct so the duplication gate has nothing to match.
func Step78(n int) int {
	return n*78 + 0
}

// Statement block 79, distinct so the duplication gate has nothing to match.
func Step79(n int) int {
	return n*79 + 7
}

// Statement block 80, distinct so the duplication gate has nothing to match.
func Step80(n int) int {
	return n*80 + 1
}

// Statement block 81, distinct so the duplication gate has nothing to match.
func Step81(n int) int {
	return n*81 + 8
}

// Statement block 82, distinct so the duplication gate has nothing to match.
func Step82(n int) int {
	return n*82 + 2
}

// Statement block 83, distinct so the duplication gate has nothing to match.
func Step83(n int) int {
	return n*83 + 9
}

// Statement block 84, distinct so the duplication gate has nothing to match.
func Step84(n int) int {
	return n*84 + 3
}
