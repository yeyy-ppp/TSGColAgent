package humaneval.correct;

public class SOLVE {
    public static String solve(int N) {
        int sum = 0;
        for (int i = 0; i < (N + "").length(); i += 1){
            sum += Integer.parseInt((N + "").substring(i, i + 1));
        }
        return Integer.toBinaryString(sum);
    }
}
