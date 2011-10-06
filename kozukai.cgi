#!/Users/nakauchiaya/.rvm/rubies/ruby-1.9.2-p136/bin/ruby
# -*- coding: utf-8 -*-

require 'date'
require 'erb'
require 'cgi'
require 'pstore'
require 'pp'

class KozukaiTyo
  def initialize
    @cgi = CGI.new('html3')
    @erb = ERB.new(input_script)
    @outcome_kozukai = {}
    @kozukai_body = {}
#    @fn = "kozukai.data"
    @fn = "/Users/nakauchiaya/Data/kozukai.data"
    @db = PStore.new(@fn)
  end

  def control
    if @cgi.params.size == 0
      @date = Date.today
      val_from_db
      viewhtml

    elsif @cgi["page_kind"] == "input"
      @date = Date.parse(@cgi["date_input"])
      val_from_cgi
      viewhtml

    elsif @cgi["page_kind"] == "date"
      @date = Date.parse(@cgi["date_input"])
      val_from_db
      viewhtml

    else
      @date = Date.today
      val_from_cgi
      viewhtml
    end
  end
  
  def val_from_db
    @db.transaction do
      need_deploy if @db["root"].size == 0
      @db["root"].each_with_index do |v,k|
        next if @date > v["date"]

        if @date == v["date"]
          set_values(v, k)
          return
        else
          default_values(k)
          return
        end
      end
      default_values(@db["root"].size)
    end
  end

  def set_values(v, k)
    @saifu_real = v["saifu_real"].to_i
    @income_kozukai, v_in_kozu = investigate_koumoku(v["income_kozukai"])
    @income_keihi, v_in_kei = investigate_koumoku(v["income_keihi"])
    @income_kei = v_in_kozu + v_in_kei
    @outcome_kozukai_t, v_out_kozu_t = investigate_koumoku(v["outcome_kozukai_t"])
    @outcome_kozukai_m, v_out_kozu_m = investigate_koumoku(v["outcome_kozukai_m"])
    @outcome_keihi_t, v_out_kei_t = investigate_koumoku(v["outcome_keihi_t"])
    @outcome_keihi_m, v_out_kei_m = investigate_koumoku(v["outcome_keihi_m"])
    @outcome_kei = v_out_kozu_t + v_out_kozu_m + v_out_kei_t + v_out_kei_m

    @inout_kei = @outcome_kei - @income_kei
    @saifu_calc = yesterday_saifu(k) - @inout_kei
    @balance = @saifu_calc - @saifu_real
    @kozukai_real = yesterday_kozukai(k) - ((v_out_kozu_t + v_out_kozu_m) - v_in_kozu)
  end

  def store_values
    today_body = now_body
    @db.transaction do
      index = -1
      (@db["root"].size-1).downto(0) do |i|
        if @db["root"][i]["date"] <= today_body["date"]
          index = i 
          break;
        end
      end
      if index == -1 
        @db["root"] << today_body
        index = @db["root"].size - 1
      elsif @db["root"][index]["date"] == today_body["date"]
        @db["root"][index] = today_body
      else
        @db["root"].insert(index, today_body)
      end
    end
  end

  def now_body
    {
      "date" => @date,
      "saifu_real" => @saifu_real,
      "kozukai_real" => @kozukai_real,
      "outcome_kozukai_t"=>@outcome_kozukai_t,
      "outcome_kozukai_m"=>@outcome_kozukai_m,
      "outcome_keihi_t"=>@outcome_keihi_t,
      "outcome_keihi_m"=>@outcome_keihi_m,
      "income_kozukai"=>@income_kozukai,
      "income_keihi"=>@income_keihi
    }
  end

  def val_from_cgi
    @db.transaction do
      index = -1
      need_deploy if @db["root"].size == 0
      @db["root"].each_with_index do |v,k|
        next if @date > v["date"]
        index = k
        if @date == v["date"]
          set_values(k, @cgi)
          @db["root"][k] = now_body
          break
        else
          set_values(k, @cgi)
#          @db["root"].insert(k) = make_body
          (@db["root"].size-1).downto(k) do |i|
            @db["root"][i+1] = @db["root"][i]
          end
          @db["root"][k] = now_body
          break
        end
      end
      if index == -1
        set_values(@db["root"].size, @cgi)
        @db["root"] << now_body
      end
    end
  end

  def yesterday_saifu(k)
    @db["root"][k-1]["saifu_real"]
  end

  def yesterday_kozukai(k)
    @db["root"][k-1]["kozukai_real"]
  end

  def investigate_koumoku(item)
    if item == nil || /項目:金額?$/ =~ item
      out_text = "項目:金額!"
    else
      out_text = item
    end

    sum = 0
#   item.chomp.split(/[\r\n]/).each do |k|
    out_text.chomp.split("\r\n").each do |k|
      item_kv = k.split(":")
      sum += item_kv[1].to_i
    end
    [out_text, sum]
  end

  def default_values(tommorow)
    @saifu_real = 0
    @income_kozukai = "項目:金額-"
    @income_keihi = "項目:金額-"
    v_in_kozu = 0
    v_in_kei = 0
    @income_kei = v_in_kozu + v_in_kei
    @outcome_kozukai_t = "項目:金額-"
    @outcome_kozukai_m = "項目:金額-"
    @outcome_keihi_t = "項目:金額-"
    @outcome_keihi_m = "項目:金額-"
    v_out_kozu_t = 0
    v_out_kozu_m = 0
    v_out_kei_t = 0
    v_out_kei_m = 0
    @outcome_kei = v_out_kozu_t + v_out_kozu_m + v_out_kei_t + v_out_kei_m

    @inout_kei = @outcome_kei - @income_kei
    @saifu_calc = yesterday_saifu(tommorow) - @inout_kei
    @balance = @saifu_calc - @saifu_real
    @kozukai_real = yesterday_kozukai(tommorow) - ((v_out_kozu_t + v_out_kozu_m) - v_in_kozu)
  end

  def viewhtml
    @cgi.out {
      @cgi.html() {
        @cgi.head {
          @cgi.title {'こづかい入力'} +
          '<META HTTP-EQUIV="content-type" CONTENT="text/html;charset=utf-8">' +
          '<link rev="MADE" href="mailto:nakauchi@mtc.biglobe.ne.jp">' +
          '<link rel="STYLESHEET" type="text/css" href="kozukai.css">'
        } + @cgi.body { build_page }
      }
    }
  end

  def build_page
    begin
      return @erb.result(binding)
    rescue
      return faild_script
    end
  end

  def dbg
    return eval(@erb.src, binding, __FILE__,__LINE__+4)
  end

  def input_script
<<EOS
    <h1>こづかい入力</h1>
    <h2>合計</h2>
    <form method="GET" action="kozukai.cgi">
      <input type="hidden" name="page_kind" value="date">
      <div> 日付: <input type="text" name="date_input" value="<%= @date %>"> 
      <input type="submit" name="change_date" value="日付変更">
    </form>
    <form method="GET" action="kozukai.cgi">
      <input type="hidden" name="page_kind" value="input">
      <input type="hidden" name="date_input" value="<%= @date %>"> 
      </div>
      <div> 財布残金: <input type="text" name="saifu_real" value="<%= @saifu_real %>"> 円 </div>
      <div> 計算残金: <%= @saifu_calc %> 円 </div>
      <div> 収支計  <%= @inout_kei %> 円 </div>
      <div> 差額    <%= @balance %> 円 </div>
      <div> 小遣い残額 <%= @kozukai_real %> 円 </div>
      <h2>収入</h2>
      <div> 
	収入計: <%= @income_kei %> 円 <br>
	小遣い: <textarea name="income_kozukai" rows="4" cols="40"> <%= @income_kozukai %> </textarea>
	経費  : <textarea name="income_keihi"   rows="4" cols="40"> <%= @income_keihi %> </textarea>
      </div>
      <h2>支出</h2>
      <div>支出計: <%= @outcome_kei %> 円 </div>
      <div>
	<h3>金額に自信がある</h3>
	小遣い: <textarea name="outcome_kozukai_t" rows="4" cols="40"><%= @outcome_kozukai_t %></textarea>
	経費:   <textarea name="outcome_keihi_t"   rows="4" cols="40"><%= @outcome_keihi_t %></textarea>
	<h3>金額がはっきりしないもの</h3>
	小遣い: <textarea name="outcome_kozukai_m" rows="4" cols="40"><%= @outcome_kozukai_m %></textarea>
	経費:   <textarea name="outcome_keihi_m"   rows="4" cols="40"><%= @outcome_keihi_m %></textarea>
      </div>
      <div> <input type="submit" value="OK"> </div>
    </form>
EOS
  end

  def faild_script
    puts "Error"
  end
end

KozukaiTyo.new.control
