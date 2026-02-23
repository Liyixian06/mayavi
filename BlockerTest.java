// BlockerTest.java
public class BlockerTest {
    public static void main(String[] args) {
        // null printer
        String s = null;
        System.out.println(s.length());
        // dead code
        if (false) {
            System.out.println("This is dead code");
        }
    }
}
