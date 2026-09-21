package humaneval.correct;

public class INTERSECTION {
    public static boolean is_prime(int num) {
        if(num == 0 || num == 1) return false;
        if(num == 2) return true;
        for(int i = 2; i <= num; i++) {
            if((num % i) == 0) return false;
        }
        return true;
    }
    public static String intersection(int[] interval1, int[] interval2) {
        int l = Math.max(interval1[0], interval2[0]);
        int r = Math.min(interval1[1], interval2[1]);
        int length = r - l;
        if(length > 0 && is_prime(length)) return "YES";
        return "NO";
    }
}
