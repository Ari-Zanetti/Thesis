package thesis.beans;

import java.util.ArrayList;
import java.util.List;
import java.util.StringTokenizer;
import org.json.simple.JSONArray;
import thesis.Language;

public class Sentence {

    private Language language;
    private String id;
    private String text;
    private int complexity;
    private List<Token> tokens;

    public Sentence(String text) {
        this.text = text.trim();
        this.tokens = new ArrayList<>();
    }

    public Language getLanguage() {
        return language;
    }

    public void setLanguage(Language language) {
        this.language = language;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text.trim();
    }

    public int getComplexity() {
        return complexity;
    }

    public void setComplexity(int complexity) {
        this.complexity = complexity;
    }

    public List<Token> getTokens() {
        return tokens;
    }

    public void setTokens(List<Token> tokens) {
        this.tokens = tokens;
    }

    public void buildTokens(String words) {
        int i = 1;
        StringTokenizer st1 = new StringTokenizer(words, "||");
        while (st1.hasMoreTokens()) {
            String group = st1.nextToken();
            StringTokenizer st = new StringTokenizer(group, "}");
            while (st.hasMoreTokens()) {
                String token = st.nextToken();
                Token t = Token.buildToken(token.substring(1));
                if (t != null) {
                    t.setGroup(i);
                    tokens.add(t);
                }
            }
            i++;
        }
    }

    public JSONArray toJSON() {
        JSONArray ar = new JSONArray();
        for (Token t : tokens) {
            ar.add(t.toJSON());
        }
        return ar;
    }

}
