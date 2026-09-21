package humaneval.correct;

public class MATCH_PARENS {
    public static boolean check(String s) {
        int val = 0;
        for(int i = 0; i < s.length(); i++) {
            if(s.charAt(i) == '(') val++;
            else val--;
            if(val < 0) return false;
        }
        return val == 0;
    }
    public static String match_parens(String[] lst) {
        String S1 = lst[0] + lst[1];
        String S2 = lst[1] + lst[0];
        if(check(S1) || check(S2)) return "Yes";
        return "No";
    }
}
