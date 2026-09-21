package humaneval.correct;

public class SKJKASDKD {
    public static boolean is_prime(int n) {
        for (int i = 2; i < (int)Math.pow(n, 0.5) + 1; i += 1) {
            if (n % i == 0) return false;
        }
        return true;
    }
    public static int skjkasdkd(int[] lst) {
        int max = 0;
        int i = 0;
        while(i < lst.length) {
            if (lst[i] > max && is_prime(lst[i]))
                max = lst[i];
            i += 1;
        }
        int result = 0;
        for (char c : (max + "").toCharArray()) {
            result += c - '0';
        }
        return result;
    }
}
