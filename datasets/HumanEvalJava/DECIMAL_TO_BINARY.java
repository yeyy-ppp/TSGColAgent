package humaneval.correct;

public class DECIMAL_TO_BINARY {
    public static String decimal_to_binary(int decimal) {
        String result = Integer.toBinaryString(decimal);
        return "db" + result + "db";
    }
}
