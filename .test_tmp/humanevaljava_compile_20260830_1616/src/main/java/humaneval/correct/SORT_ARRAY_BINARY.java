package humaneval.correct;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;

public class SORT_ARRAY_BINARY {
   public static int number_ones(int n) {
      if(n < 0) n *= -1;
      int count = 0;
      while(n > 0) {
         count += n & 1;
         n >>= 1;
      }
      return count;
   }
   public static ArrayList<Integer> sort_array_binary(ArrayList<Integer> arr) {
      Collections.sort(arr, new Comparator<Integer>() {
         @Override
         public int compare(Integer o1, Integer o2) {
            int num_ones_o1 = number_ones(o1);
            int num_ones_o2 = number_ones(o2);
            if(num_ones_o1 == num_ones_o2) {
               if(o1 == o2) return 0;
               if(o1 < o2) return -1;
               if(o1 > o2) return 1;
            }
            if(num_ones_o1 < num_ones_o2) return -1;
            else return 1;
         }
      });
      return arr;
   }
}
