package humaneval.correct;

import java.math.BigDecimal;
import java.math.RoundingMode;

public class ISCUBE {
    public static boolean iscube(int a) {
        a = Math.abs(a);
        double root = Math.pow(a, 1./3);
        BigDecimal bd = BigDecimal.valueOf(root);
        int round_root = (int) bd.setScale(0, RoundingMode.HALF_UP).doubleValue();
        return ((int) Math.pow(round_root, 3)) == a;
    }
}
