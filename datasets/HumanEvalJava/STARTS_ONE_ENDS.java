package humaneval.correct;

public class STARTS_ONE_ENDS {
    public static int starts_one_ends(int n) {
        if (n == 1)
            return 1;
        return (int) ((10 + 9 - 1) * Math.pow(10, n - 2));
    }
}
