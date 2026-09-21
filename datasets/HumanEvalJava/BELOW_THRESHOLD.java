package humaneval.correct;

public class BELOW_THRESHOLD {
    public static boolean below_threshold(int[] l, int t) {
        for (int i = 0; i < l.length; i += 1) {
            if (l[i] >= t)
                return false;
        }
        return true;
    }
}
