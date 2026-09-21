package humaneval.correct;

public class CHANGE_BASE {
    public static String change_base(int x, int base) {
        String result = "";
        while (x > 0) {
            result = (x % base) + result;
            x = (int) x / base;
        }
        return result;
    }
}
