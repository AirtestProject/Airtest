from airtest.report import report


class PocoReport(report.LogToHtml):

    def translate(self, step):
        if step["is_poco"] is True:
            return self.translate_poco_step(step)
        else:
            return super(PocoReport, self).translate(step)

    def translate_poco_step(self, step):
        """
        处理poco的相关操作，参数与airtest的不同，由一个截图和一个操作构成，需要合成一个步骤
        Parameters
        ----------
        step 一个完整的操作，如click
        prev_step 前一个步骤，应该是截图

        Returns
        -------

        """
        ret = {}
        prev_step = self._steps[-1]
        if prev_step:
            ret.update(prev_step)
        ret['type'] = step[1].get("name", "")
        if step.get('trace'):
            ret['trace'] = step['trace']
            ret['traceback'] = step.get('traceback')
        if ret['type'] == 'touch':
            # 取出点击位置
            if step[1]['args'] and len(step[1]['args'][0]) == 2:
                pos = step[1]['args'][0]
                ret['target_pos'] = [int(pos[0]), int(pos[1])]
                ret['top'] = ret['target_pos'][1]
                ret['left'] = ret['target_pos'][0]
        elif ret['type'] == 'swipe':
            if step[1]['args'] and len(step[1]['args'][0]) == 2:
                pos = step[1]['args'][0]
                ret['target_pos'] = [int(pos[0]), int(pos[1])]
                ret['top'] = ret['target_pos'][1]
                ret['left'] = ret['target_pos'][0]
            # swipe 需要显示一个方向
            vector = step[1]["kwargs"].get("vector")
            if vector:
                ret['swipe'] = self.dis_vector(vector)
                ret['vector'] = vector

        ret['desc'] = self.func_desc_poco(ret)
        ret['title'] = self._translate_title(ret)
        return ret

    def func_desc_poco(self, step):
        """ 把对应的poco操作显示成中文"""
        desc = {
            "touch": u"点击UI组件 {name}".format(name=step.get("text", "")),
        }
        if step['type'] in desc:
            return desc.get(step['type'])
        else:
            return self._translate_desc(step)


if __name__ == "__main__":
    report.LogToHtml = PocoReport
    import argparse
    ap = argparse.ArgumentParser()
    args = report.get_parger(ap).parse_args()
    report.main(args)
