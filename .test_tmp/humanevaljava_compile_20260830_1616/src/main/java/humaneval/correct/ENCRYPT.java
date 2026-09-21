package humaneval.correct;

public class ENCRYPT {
    public static String encrypt(String s) {
        StringBuilder sb = new StringBuilder();
        String d = "abcdefghijklmnopqrstuvwxyz";
        for (char c : s.toCharArray()){
            if ('a' <= c && c <= 'z'){
                sb.append(
                    d.charAt((d.indexOf((int) c) + 2 * 2) % 26)
                );
            } else {
                sb.append(c);
            }
        }
        return sb.toString();
    }
}
