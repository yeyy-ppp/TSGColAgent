package humaneval.correct;

public class MULTIPLY {
    public static int multiply(int a, int b) {
        return Math.abs(a % 10) * Math.abs(b % 10);
    }
}
